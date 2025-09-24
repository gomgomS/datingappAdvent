from pymongo import MongoClient, ASCENDING, UpdateOne

MAIN_DB_NAME = "datingapp"
MAIN_DB_URI = "mongodb://127.0.0.1:27017/" + MAIN_DB_NAME

DEFAULT_PLANS = [
    {
        "plan": "premium",
        "DAILY_SWIPE": 8,
        "CAN_UNDO_LAST_DISLIKE": True,
        "CAN_SEE_WHO_LIKE_USER": True,
        "CAN_UPLOAD_ALBUM": True,
        "MORE_OFTEN_SEEN": True,
        "GET_INFO_TOTAL_NEW_USER": True,
        "CAN_FILTER": True,
    },
    {
        "plan": "free",
        "DAILY_SWIPE": 70,
        "CAN_UNDO_LAST_DISLIKE": False,
        "CAN_SEE_WHO_LIKE_USER": False,
        "CAN_UPLOAD_ALBUM": False,
        "MORE_OFTEN_SEEN": False,
        "GET_INFO_TOTAL_NEW_USER": False,
        "CAN_FILTER": False,
    },
]

CITY_LIST = [
    "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang",
    "Palembang", "Makassar", "Bogor", "Depok", "Bekasi",
    "Yogyakarta", "Malang", "Padang", "Pekanbaru", "Banjarmasin",
    "Samarinda", "Pontianak", "Manado", "Denpasar", "Batam",
    "Tangerang", "South Tangerang", "Bandar Lampung", "Cimahi", "Tasikmalaya",
    "Serang", "Balikpapan", "Jambi", "Cirebon", "Surakarta",
    "Kupang", "Mataram", "Jayapura", "Bengkulu", "Palu",
    "Ambon", "Kendari", "Dumai", "Pekalongan", "Palangka Raya",
    "Binjai", "Kediri", "Sorong", "Tegal", "Banda Aceh",
    "Tarakan", "Probolinggo", "Singkawang", "Lubuklinggau", "Tanjungpinang",
    "Bitung", "Pangkalpinang", "Batu", "Pasuruan", "Banjar",
    "Gorontalo", "Ternate", "Madiun", "Salatiga", "Prabumulih",
    "Lhokseumawe", "Langsa", "Bontang", "Tanjungbalai", "Tebing Tinggi",
    "Metro", "Palopo", "Bima", "Baubau", "Parepare",
    "Blitar", "Pagar Alam", "Payakumbuh", "Gunungsitoli", "Mojokerto",
    "Bukittinggi", "Kotamobagu", "Magelang", "Tidore", "Tomohon",
    "Sungai Penuh", "Subulussalam", "Pariaman", "Sibolga", "Tual",
    "Solok", "Sawahlunto", "Padang Panjang", "Sabang", "Timika"
]


def ensure_indexes(db):
    db.db_subscription_config.create_index([("plan", ASCENDING)], unique=True)
    db.db_city_list.create_index([("name", ASCENDING)], unique=True)


def seed_plans(db):
    ops = []
    for plan in DEFAULT_PLANS:
        ops.append(UpdateOne({"plan": plan["plan"]}, {"$set": plan}, upsert=True))
    if ops:
        result = db.db_subscription_config.bulk_write(ops, ordered=False)
        print(
            f"Subscription upserts: matched={result.matched_count} upserted={len(result.upserted_ids)} modified={result.modified_count}"
        )


def seed_cities(db):
    ops = []
    for name in CITY_LIST:
        ops.append(UpdateOne({"name": name}, {"$set": {"name": name}}, upsert=True))
    if ops:
        result = db.db_city_list.bulk_write(ops, ordered=False)
        print(
            f"City upserts: matched={result.matched_count} upserted={len(result.upserted_ids)} modified={result.modified_count}"
        )


def main():
    client = MongoClient(MAIN_DB_URI)
    db = client[MAIN_DB_NAME]
    ensure_indexes(db)
    seed_plans(db)
    seed_cities(db)
    print("Seeding complete.")


if __name__ == "__main__":
    main()


