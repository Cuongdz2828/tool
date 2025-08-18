import requests
import time
import os
import uuid
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from colorama import Fore, init

init(autoreset=True)

room_names_map = {
    "1": "Nhà Kho",
    "2": "Phòng Họp",
    "3": "Phòng Giám Đốc",
    "4": "Phòng Trò Chuyện",
    "5": "Phòng Giám Sát",
    "6": "Văn Phòng",
    "7": "Phòng Tài Vụ",
    "8": "Phòng Nhân Sự",
}

# ================== QUẢN LÝ THIẾT BỊ & KEY ==================
def get_device_id():
    file_path = ".sconfig"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            device_id = f.read().strip()
            if device_id:
                print(f"📌 Device ID hiện tại: {device_id}")
                return device_id
    raw_suffix = uuid.uuid4().hex.upper()[:10]
    device_id = "DEVICE-" + raw_suffix
    with open(file_path, "w") as f:
        f.write(device_id)
    print(f"📌 Device ID mới tạo: {device_id}")
    return device_id

def kiem_tra_quyen_truy_cap(device_id):
    while True:
        print("\n" + "="*50)
        print(f"Mã thiết bị: {device_id}")
        print("="*50)
        try:
            url_key = "https://raw.githubusercontent.com/Cuongdz2828/pt/main/test/a.txt"
            ds_key_raw = requests.get(url_key, timeout=5).text.strip().splitlines()
        except Exception as e:
            print(f"⚠️ Lỗi khi tải key: {e}")
            time.sleep(3)
            continue
        
        key_nhap = input("Nhập Key VIP: ").strip()
        hop_le = False
        dev_local = device_id.replace("DEVICE-", "").strip().upper()

        for dong in ds_key_raw:
            parts = [p.strip() for p in dong.split("|")]
            if len(parts) >= 4:
                device, key, _, ngay_hh = parts
                dev_file = device.replace("DEVICE-", "").strip().upper()
                if dev_file == dev_local and key.strip() == key_nhap.strip():
                    try:
                        ngay_hh_dt = datetime.strptime(ngay_hh, "%d/%m/%Y")
                        if datetime.now() <= ngay_hh_dt:
                            hop_le = True
                            break
                        else:
                            print("❌ Key đã hết hạn!")
                    except:
                        pass

        if hop_le:
            print(Fore.GREEN + "✅ Key VIP còn hiệu lực!\n")
            break
        else:
            print(Fore.RED + "❌ Key hoặc mã thiết bị không đúng.")
            input("Nhấn Enter để thử lại...")

# ================== API GAME ==================
def fetch_data(url, headers):
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                return data["data"]
            else:
                print("❌ API trả về:", data)
        else:
            print(f"❌ Lỗi HTTP {r.status_code} khi gọi {url}")
        return None
    except Exception as e:
        print(f"⚠️ Lỗi fetch_data: {e}")
        return None

def analyze_data(headers, asset_mode):
    url_recent_10 = f"https://api.escapemaster.net/escape_game/recent_10_issues?asset={asset_mode}"
    url_recent_100 = f"https://api.escapemaster.net/escape_game/recent_100_issues?asset={asset_mode}"
    data_10 = fetch_data(url_recent_10, headers)
    data_100 = fetch_data(url_recent_100, headers)

    if not data_10 or not data_100:
        return None, [], "?", {}

    current_issue_id = data_10[0].get("issue_id")
    killed_room_id = str(data_10[0].get("killed_room_id"))
    current_killed_room = room_names_map.get(killed_room_id, f"Phòng #{killed_room_id}")

    # 100 trận gần nhất
    rates_100 = {}
    stats_100 = data_100.get("room_id_2_killed_times", {})
    for rid, name in room_names_map.items():
        count = stats_100.get(rid, 0)
        rates_100[rid] = 100 - (count / 100 * 100)

    sorted_rooms = sorted(rates_100.items(), key=lambda x: x[1], reverse=True)
    return current_issue_id, sorted_rooms, current_killed_room, rates_100

# ================== ĐẶT CƯỢC ==================
def place_bet(headers, asset, issue_id, room_id, bet_amount):
    url = "https://api.escapemaster.net/escape_game/bet"
    payload = {
        "asset_type": asset,       # fix: dùng asset_type
        "issue_id": str(issue_id),
        "room_id": int(room_id),   # room_id 1..8
        "bet_amount": bet_amount
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        data = r.json()
        print("📥 KQ đặt cược:", data)
        if r.status_code == 200 and data.get("code") == 0:
            print(Fore.GREEN + f"✅ Đặt cược thành công {bet_amount} {asset} vào phòng {room_id} (Kỳ {issue_id})")
            return True
        else:
            print(Fore.RED + f"❌ Lỗi đặt cược: {data.get('msg')}")
    except Exception as e:
        print(Fore.RED + f"⚠️ Exception khi đặt cược: {e}")
    return False

# ================== VÍ ==================
def show_wallet(headers):
    url = "https://wallet.3games.io/api/wallet/user_asset"
    try:
        r = requests.post(url, headers=headers, timeout=10)
        if r.status_code == 200:
            vi_data = r.json()
            balances = {"USDT": 0.0, "WORLD": 0.0, "BUILD": 0.0, "ENERGY": 0.0, "BTC": 0.0}
            if vi_data.get("code") == 0:
                data = vi_data.get("data", {})
                if isinstance(data, dict) and "user_asset" in data:
                    ua = data["user_asset"]
                    for k, v in ua.items():
                        if k in balances:
                            balances[k] = 0.0 if v is None else v
            print(
                Fore.LIGHTGREEN_EX
                + f"SỐ DƯ:\n"
                + f"USDT: {balances['USDT']}   "
                + f"WORLD: {balances['WORLD']}   "
                + f"BUILD: {balances['BUILD']}   "
                + f"ENERGY: {balances['ENERGY']}   "
                + f"BTC: {balances['BTC']}\n"
            )
            return balances
        else:
            print(f"❌ API ví lỗi HTTP {r.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ Lỗi ví: {e}")
        return {}

# ================== MAIN ==================
if __name__ == "__main__":
    device_id = get_device_id()
    kiem_tra_quyen_truy_cap(device_id)

    link = input("Dán link battleroyale: ").strip()
    parsed = urlparse(link)
    params = parse_qs(parsed.query)
    user_id = params.get("userId", [""])[0]
    secret_key = params.get("secretKey", [""])[0]
    headers = {"User-Id": user_id, "User-Secret-Key": secret_key}

    print(Fore.CYAN + "═"*40)
    print(Fore.YELLOW + "   CHỌN CHẾ ĐỘ")
    print(Fore.CYAN + "═"*40)
    print("1. BUILD")
    print("2. USDT")
    choice = input("Chọn (1-2): ")
    asset_mode = {"1": "BUILD", "2": "USDT"}.get(choice, "BUILD")

    try:
        bet_amount = float(input("Nhập số tiền cược mỗi trận: ").strip())
    except:
        bet_amount = 30.0

    total_games, total_wins = 0, 0
    win_streak = 0
    profit = 0
    pending_issue, pending_room = None, None

    while True:
        current_issue, sorted_rooms, killed_room, rates_100 = analyze_data(headers, asset_mode)

        if not current_issue:
            print(Fore.RED + "Không lấy được dữ liệu API...")
            time.sleep(5)
            continue

        # ==== Kết quả kỳ trước ====
        if pending_issue and str(pending_issue) == str(current_issue):
            total_games += 1
            if killed_room != pending_room:
                total_wins += 1
                win_streak += 1
                profit += bet_amount
                print(Fore.GREEN + f"🎉 Kỳ {current_issue}: THẮNG (AI chọn {pending_room}, Sát thủ: {killed_room})")
            else:
                win_streak = 0
                profit -= bet_amount
                print(Fore.RED + f"💀 Kỳ {current_issue}: THUA (AI chọn {pending_room}, Sát thủ: {killed_room})")
            pending_issue, pending_room = None, None
            time.sleep(2)

        pred_id = str(int(current_issue) + 1)

        print(Fore.CYAN + f"\n🔎 Đang phân tích kỳ {current_issue}")
        if sorted_rooms:
            best_room_id, best_rate = sorted_rooms[0]
            best_room_name = room_names_map.get(str(best_room_id), f"Phòng #{best_room_id}")

            print(Fore.MAGENTA + f"🎯 Phòng được chọn: {best_room_name}")
            print(Fore.GREEN + f"Độ tin cậy: {best_rate:.1f}%")

            # ==== Thống kê ====
            win_rate = (total_wins / total_games * 100) if total_games else 0
            print(Fore.YELLOW + f"\n📊 Thống kê:")
            print(Fore.YELLOW + f"   Tổng trận: {total_games}")
            print(Fore.YELLOW + f"   Thắng: {total_wins}")
            print(Fore.YELLOW + f"   Chuỗi thắng: {win_streak}")
            print(Fore.YELLOW + f"   Tỉ lệ thắng: {win_rate:.2f}%")
            print(Fore.YELLOW + f"   Lời/Lỗ: {profit} {asset_mode}\n")

            # ==== Đặt cược ====
            success = place_bet(headers, asset_mode, pred_id, int(best_room_id), bet_amount)
            if success:
                pending_issue, pending_room = pred_id, str(best_room_id)

        # ==== Hiển thị sát thủ rõ ràng ====
        print(Fore.RED + f"🔪 Sát thủ kỳ {current_issue}: {killed_room}\n")

        show_wallet(headers)

        countdown = 1
        while True:
            time.sleep(1)
            print(Fore.YELLOW + f"⏳ Đang chờ kỳ mới... {countdown}s", end="\r")
            countdown += 1
            new_issue, _, _, _ = analyze_data(headers, asset_mode)
            if new_issue and new_issue != current_issue:
                print(Fore.GREEN + "\n🎉 Có kỳ mới! Đang xử lý...")
                break
