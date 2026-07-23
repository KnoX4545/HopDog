# vote_storage.py - ذخیره‌سازی رای‌های میو در دیتابیس Supabase (نسخه کامل)

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from database import supabase

logger = logging.getLogger(__name__)


# ================================================================
# کلاس اصلی VoteStorage
# ================================================================

class VoteStorage:
    """
    مدیریت ذخیره‌سازی و بازیابی رای‌های میو در دیتابیس Supabase
    
    ساختار جدول votes در Supabase:
    CREATE TABLE votes (
        vote_key TEXT PRIMARY KEY,
        data JSONB NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    TABLE_NAME = "votes"
    
    @staticmethod
    def save_vote(vote_key: str, data: Dict[str, Any]) -> bool:
        """
        ذخیره یک رای جدید در دیتابیس
        
        Args:
            vote_key: کلید یکتای رای (مثلاً chatId_userId_timestamp)
            data: دیکشنری حاوی اطلاعات رای
        
        Returns:
            bool: موفقیت‌آمیز بودن ذخیره‌سازی
        """
        try:
            # استخراج زمان انقضا از داده‌ها
            expires_at = data.get("until")
            if expires_at:
                # اگر timestamp بود، به datetime تبدیل کن
                if isinstance(expires_at, (int, float)):
                    expires_at = datetime.fromtimestamp(expires_at)
                elif isinstance(expires_at, str):
                    try:
                        expires_at = datetime.fromisoformat(expires_at)
                    except:
                        expires_at = datetime.now() + timedelta(minutes=5)
            else:
                # پیش‌فرض: 5 دقیقه
                expires_at = datetime.now() + timedelta(minutes=5)
            
            # داده‌ها رو به JSON تبدیل کن
            data_json = json.dumps(data, ensure_ascii=False, default=str)
            
            # ذخیره در دیتابیس
            supabase.table(VoteStorage.TABLE_NAME).upsert({
                "vote_key": vote_key,
                "data": data_json,
                "expires_at": expires_at.isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()
            
            logger.info(f"✅ رای {vote_key} در دیتابیس ذخیره شد")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در ذخیره رای {vote_key}: {e}")
            return False
    
    @staticmethod
    def get_vote(vote_key: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک رای از دیتابیس
        
        Args:
            vote_key: کلید یکتای رای
        
        Returns:
            Optional[Dict]: دیکشنری اطلاعات رای یا None اگر وجود نداشته باشد
        """
        try:
            response = supabase.table(VoteStorage.TABLE_NAME) \
                .select("data") \
                .eq("vote_key", vote_key) \
                .execute()
            
            if response.data and len(response.data) > 0:
                data_str = response.data[0].get("data")
                if data_str:
                    data = json.loads(data_str)
                    logger.info(f"✅ رای {vote_key} از دیتابیس بازیابی شد")
                    return data
            
            logger.warning(f"⚠️ رای {vote_key} در دیتابیس یافت نشد")
            return None
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت رای {vote_key}: {e}")
            return None
    
    @staticmethod
    def delete_vote(vote_key: str) -> bool:
        """
        حذف یک رای از دیتابیس
        
        Args:
            vote_key: کلید یکتای رای
        
        Returns:
            bool: موفقیت‌آمیز بودن حذف
        """
        try:
            supabase.table(VoteStorage.TABLE_NAME) \
                .delete() \
                .eq("vote_key", vote_key) \
                .execute()
            
            logger.info(f"🗑️ رای {vote_key} از دیتابیس حذف شد")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در حذف رای {vote_key}: {e}")
            return False
    
    @staticmethod
    def cleanup_expired() -> int:
        """
        پاک‌سازی رای‌های منقضی شده از دیتابیس
        
        Returns:
            int: تعداد رای‌های حذف شده
        """
        try:
            now = datetime.now().isoformat()
            
            # ابتدا تعداد رای‌های منقضی شده رو بشمار
            count_response = supabase.table(VoteStorage.TABLE_NAME) \
                .select("vote_key", count="exact") \
                .lt("expires_at", now) \
                .execute()
            
            count = count_response.count if hasattr(count_response, 'count') else 0
            
            # حذف رای‌های منقضی شده
            if count > 0:
                supabase.table(VoteStorage.TABLE_NAME) \
                    .delete() \
                    .lt("expires_at", now) \
                    .execute()
                
                logger.info(f"🧹 {count} رای منقضی شده از دیتابیس پاک شد")
            else:
                logger.debug("🧹 هیچ رای منقضی شده‌ای برای پاک‌سازی وجود نداشت")
            
            return count
            
        except Exception as e:
            logger.error(f"❌ خطا در پاک‌سازی رای‌های منقضی شده: {e}")
            return 0
    
    @staticmethod
    def get_active_votes(limit: int = 100) -> List[Dict[str, Any]]:
        """
        دریافت لیست رای‌های فعال (غیرمنقضی)
        
        Args:
            limit: حداکثر تعداد
        
        Returns:
            List[Dict]: لیست رای‌های فعال
        """
        try:
            now = datetime.now().isoformat()
            
            response = supabase.table(VoteStorage.TABLE_NAME) \
                .select("vote_key, data, expires_at") \
                .gt("expires_at", now) \
                .limit(limit) \
                .execute()
            
            if response.data:
                votes = []
                for row in response.data:
                    try:
                        data = json.loads(row.get("data", "{}"))
                        votes.append({
                            "vote_key": row.get("vote_key"),
                            "data": data,
                            "expires_at": row.get("expires_at")
                        })
                    except:
                        continue
                
                logger.info(f"📋 {len(votes)} رای فعال در دیتابیس یافت شد")
                return votes
            
            return []
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت رای‌های فعال: {e}")
            return []
    
    @staticmethod
    def vote_exists(vote_key: str) -> bool:
        """
        بررسی وجود یک رای در دیتابیس
        
        Args:
            vote_key: کلید یکتای رای
        
        Returns:
            bool: وجود یا عدم وجود رای
        """
        try:
            response = supabase.table(VoteStorage.TABLE_NAME) \
                .select("vote_key") \
                .eq("vote_key", vote_key) \
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"❌ خطا در بررسی وجود رای {vote_key}: {e}")
            return False
    
    @staticmethod
    def update_vote_data(vote_key: str, new_data: Dict[str, Any]) -> bool:
        """
        به‌روزرسانی داده‌های یک رای
        
        Args:
            vote_key: کلید یکتای رای
            new_data: داده‌های جدید
        
        Returns:
            bool: موفقیت‌آمیز بودن به‌روزرسانی
        """
        try:
            # داده‌های فعلی رو بگیر
            current_data = VoteStorage.get_vote(vote_key)
            if not current_data:
                logger.warning(f"⚠️ رای {vote_key} برای به‌روزرسانی یافت نشد")
                return False
            
            # داده‌ها رو با هم ادغام کن
            merged_data = {**current_data, **new_data}
            
            # ذخیره کن
            return VoteStorage.save_vote(vote_key, merged_data)
            
        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی رای {vote_key}: {e}")
            return False
    
    @staticmethod
    def add_vote_to_vote(vote_key: str, voter_id: int) -> bool:
        """
        اضافه کردن یک رای به رای‌گیری میو
        
        Args:
            vote_key: کلید یکتای رای
            voter_id: آیدی کاربری که رای داده
        
        Returns:
            bool: موفقیت‌آمیز بودن اضافه شدن رای
        """
        try:
            # داده‌های فعلی رو بگیر
            data = VoteStorage.get_vote(vote_key)
            if not data:
                return False
            
            # لیست رای‌دهنده‌ها رو به‌روز کن
            if "votes" not in data:
                data["votes"] = []
            
            if str(voter_id) in data["votes"]:
                logger.warning(f"⚠️ کاربر {voter_id} قبلاً به رای {vote_key} رای داده")
                return False
            
            data["votes"].append(str(voter_id))
            
            # ذخیره کن
            return VoteStorage.save_vote(vote_key, data)
            
        except Exception as e:
            logger.error(f"❌ خطا در اضافه کردن رای به {vote_key}: {e}")
            return False
    
    @staticmethod
    def get_vote_count(vote_key: str) -> int:
        """
        دریافت تعداد رای‌های یک رای‌گیری
        
        Args:
            vote_key: کلید یکتای رای
        
        Returns:
            int: تعداد رای‌ها
        """
        data = VoteStorage.get_vote(vote_key)
        if data:
            return len(data.get("votes", []))
        return 0
    
    @staticmethod
    def is_vote_expired(vote_key: str) -> bool:
        """
        بررسی منقضی شدن یک رای
        
        Args:
            vote_key: کلید یکتای رای
        
        Returns:
            bool: منقضی شده یا نه
        """
        try:
            response = supabase.table(VoteStorage.TABLE_NAME) \
                .select("expires_at") \
                .eq("vote_key", vote_key) \
                .execute()
            
            if response.data and len(response.data) > 0:
                expires_at_str = response.data[0].get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    return expires_at < datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در بررسی انقضای رای {vote_key}: {e}")
            return True
    
    @staticmethod
    def get_remaining_time(vote_key: str) -> int:
        """
        دریافت زمان باقی‌مانده تا انقضای رای (به ثانیه)
        
        Args:
            vote_key: کلید یکتای رای
        
        Returns:
            int: زمان باقی‌مانده به ثانیه (0 اگر منقضی شده باشد)
        """
        try:
            response = supabase.table(VoteStorage.TABLE_NAME) \
                .select("expires_at") \
                .eq("vote_key", vote_key) \
                .execute()
            
            if response.data and len(response.data) > 0:
                expires_at_str = response.data[0].get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    remaining = (expires_at - datetime.now()).total_seconds()
                    return max(0, int(remaining))
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت زمان باقی‌مانده رای {vote_key}: {e}")
            return 0


# ================================================================
# توابع کمکی برای کار با رای‌های میو
# ================================================================

def create_meow_vote_key(chat_id: int, user_id: int) -> str:
    """
    ایجاد کلید یکتا برای رای میو
    
    Args:
        chat_id: آیدی گروه
        user_id: آیدی کاربر متخلف
    
    Returns:
        str: کلید یکتا
    """
    import time
    return f"meow_{chat_id}_{user_id}_{int(time.time() * 1000)}"


def create_meow_vote_data(target_id: int, chat_id: int, duration: int = 60) -> Dict[str, Any]:
    """
    ایجاد داده‌های اولیه برای رای میو
    
    Args:
        target_id: آیدی کاربر متخلف
        chat_id: آیدی گروه
        duration: مدت زمان رای‌گیری به ثانیه (پیش‌فرض 60)
    
    Returns:
        Dict: داده‌های رای
    """
    now = datetime.now().timestamp()
    return {
        "target_id": target_id,
        "chat_id": chat_id,
        "votes": [],
        "until": now + duration,
        "created_at": now,
        "duration": duration,
        "status": "active"  # active, expired, resolved
    }


def is_meow_vote_active(vote_data: Dict[str, Any]) -> bool:
    """
    بررسی فعال بودن رای میو
    
    Args:
        vote_data: داده‌های رای
    
    Returns:
        bool: فعال بودن یا نه
    """
    if not vote_data:
        return False
    
    if vote_data.get("status") != "active":
        return False
    
    until = vote_data.get("until", 0)
    return datetime.now().timestamp() < until


def get_meow_vote_result(vote_data: Dict[str, Any], needed_votes: int = 3) -> Dict[str, Any]:
    """
    دریافت نتیجه رای میو
    
    Args:
        vote_data: داده‌های رای
        needed_votes: تعداد رای‌های لازم
    
    Returns:
        Dict: نتیجه رای
    """
    if not vote_data:
        return {"status": "invalid", "message": "رای وجود ندارد"}
    
    if vote_data.get("status") != "active":
        return {"status": "expired", "message": "رای به پایان رسیده"}
    
    votes = vote_data.get("votes", [])
    vote_count = len(votes)
    
    if vote_count >= needed_votes:
        return {
            "status": "passed",
            "message": f"✅ با {vote_count} رای، کاربر به زندان فرستاده شد!",
            "vote_count": vote_count,
            "needed": needed_votes
        }
    
    until = vote_data.get("until", 0)
    remaining = max(0, int(until - datetime.now().timestamp()))
    
    return {
        "status": "active",
        "message": f"⏳ {remaining} ثانیه مونده - {vote_count}/{needed_votes} رای",
        "vote_count": vote_count,
        "needed": needed_votes,
        "remaining": remaining
    }


# ================================================================
# نمونه‌های تست
# ================================================================

if __name__ == "__main__":
    # تست ذخیره‌سازی
    import time
    
    # تنظیم لاگ
    logging.basicConfig(level=logging.INFO)
    
    # تست 1: ذخیره رای
    vote_key = create_meow_vote_key(123456789, 987654321)
    vote_data = create_meow_vote_data(987654321, 123456789)
    
    print("🧪 تست ذخیره رای...")
    result = VoteStorage.save_vote(vote_key, vote_data)
    print(f"✅ ذخیره شد: {result}")
    
    # تست 2: دریافت رای
    print("\n🧪 تست دریافت رای...")
    data = VoteStorage.get_vote(vote_key)
    print(f"✅ داده‌ها: {data}")
    
    # تست 3: اضافه کردن رای
    print("\n🧪 تست اضافه کردن رای...")
    result = VoteStorage.add_vote_to_vote(vote_key, 111111111)
    print(f"✅ اضافه شد: {result}")
    
    # تست 4: تعداد رای‌ها
    print("\n🧪 تست تعداد رای‌ها...")
    count = VoteStorage.get_vote_count(vote_key)
    print(f"✅ تعداد رای‌ها: {count}")
    
    # تست 5: زمان باقی‌مانده
    print("\n🧪 تست زمان باقی‌مانده...")
    remaining = VoteStorage.get_remaining_time(vote_key)
    print(f"✅ زمان باقی‌مانده: {remaining} ثانیه")
    
    # تست 6: حذف رای
    print("\n🧪 تست حذف رای...")
    result = VoteStorage.delete_vote(vote_key)
    print(f"✅ حذف شد: {result}")
    
    print("\n🎉 همه تست‌ها با موفقیت انجام شد!")
