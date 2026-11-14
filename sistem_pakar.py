import json
import sys
import os
import textwrap

def muat_basis_pengetahuan(nama_file="kb_padi.json"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_lengkap = os.path.join(base_dir, nama_file)
    if not os.path.exists(path_lengkap):
        path_lengkap = nama_file
        
    if not os.path.exists(path_lengkap):
        print(f"Error: File basis pengetahuan '{nama_file}' tidak ditemukan.")
        sys.exit(1)
    with open(path_lengkap, "r", encoding="utf-8") as f:
        return json.load(f)

def cari_fakta_tanya(kb):
    """
    Fakta yang tidak pernah menjadi hasil aturan (maka) adalah fakta input
    yang harus ditanyakan ke pengguna.
    """
    semua_hasil = {aturan["maka"] for aturan in kb["aturan"]}
    fakta_tanya = []
    
    for aturan in kb["aturan"]:
        for premis in aturan["jika"]:
            if premis not in semua_hasil and premis not in fakta_tanya:
                fakta_tanya.append(premis)
    return fakta_tanya

def format_pertanyaan(fakta):
    mapping_teks = {
        "batang tanaman berlubang atau pangkal patah": "Apakah batang tanaman padi terlihat berlubang gerekan atau pangkal batang mudah patah?",
        "titik tumbuh pucuk daun mati menggulung mengering": "Apakah titik tumbuh pucuk daun menguning, menggulung, dan mati mengering?",
        "tanaman padi masih berada pada fase vegetatif anakan": "Apakah tanaman padi saat ini masih berada pada fase vegetatif (pembentukan anakan)?",
        "rumpun padi menguning kecokelatan mengering melingkar seperti terbakar": "Apakah rumpun padi menguning kecokelatan dan mengering melingkar seperti bekas terbakar (hopperburn)?",
        "terdapat koloni serangga kecil cokelat di pangkal batang": "Apakah terlihat koloni serangga kecil bersayap/tidak bersayap berwarna cokelat di pangkal batang padi?",
        "terdapat cairan manis embun jelaga hitam dan populasi serangga padat": "Apakah terdapat bercak embun jelaga hitam pada pangkal batang dan populasi serangga sangat padat?",
        "terdapat bercak lonjong keabu-abuan dengan tepi cokelat pada pelepah dekat permukaan air": "Apakah terlihat bercak lonjong keabu-abuan bertepi cokelat pada pelepah daun dekat permukaan air?",
        "bercak merambat meluas ke pelepah daun bagian atas": "Apakah bercak pada pelepah tersebut merambat naik dan meluas ke helaian daun atas?",
        "terdapat bercak daun berbentuk belah ketupat dengan ujung meruncing": "Apakah terdapat bercak pada helaian daun berbentuk belah ketupat dengan ujung meruncing?",
        "bagian tengah bercak berwarna kelabu keputihan": "Apakah bagian tengah dari bercak daun tersebut berwarna kelabu keputihan?"
    }
    return mapping_teks.get(fakta, f"Apakah {fakta}?")

def jalankan_forward_chaining(kb, fakta_awal):
    """
    Mesin inferensi Forward Chaining:
    Mulai dari fakta yang diketahui, cari aturan yang syaratnya terpenuhi,
    tambahkan hasilnya ke memori, catat sumber dan alasan penelusuran.
    """
    memori = set(fakta_awal)
    jejak_alasan = {}
    siklus_log = []
    
    semua_kesimpulan_akhir = {
        aturan["maka"] for aturan in kb["aturan"] 
        if aturan["id"] in ["R3", "R4", "R5", "R6"]
    }
    
    siklus = 1
    while True:
        cocok = []
        for aturan in kb["aturan"]:
            hasil = aturan["maka"]
            if hasil in memori:
                continue
            
            mode = aturan.get("mode", "dan").lower()
            syarat = aturan["jika"]
            
            if mode == "dan":
                terpenuhi = all(s in memori for s in syarat)
            elif mode == "atau":
                terpenuhi = any(s in memori for s in syarat)
            else:
                terpenuhi = False
                
            if terpenuhi:
                cocok.append(aturan)
        
        if not cocok:
            siklus_log.append(f"Siklus {siklus}: tidak ada aturan baru, berhenti")
            break
            
        r = cocok[0]
        hasil_r = r["maka"]
        memori.add(hasil_r)
        
        premis_aktif = [s for s in r["jika"] if s in memori]
        jejak_alasan[hasil_r] = {
            "id": r["id"],
            "premis": premis_aktif,
            "sumber": r["sumber"]
        }
        siklus_log.append(f"Siklus {siklus}: {r['id']} -> {hasil_r}")
        siklus += 1
        
    kesimpulan_ditemukan = [k for k in memori if k in semua_kesimpulan_akhir]
    return kesimpulan_ditemukan, jejak_alasan, siklus_log

def cetak_alasan_rekursif(item, jejak_alasan, indent="  "):
    if item not in jejak_alasan:
        return
    info = jejak_alasan[item]
    premis_str = ", ".join(info["premis"])
    print(f"{indent}{item} <- {info['id']} ({premis_str}) [Sumber: {info['sumber']}]")
    for p in info["premis"]:
        cetak_alasan_rekursif(p, jejak_alasan, indent + "    ")

def main():
    kb = muat_basis_pengetahuan("kb_padi.json")
    fakta_tanya = cari_fakta_tanya(kb)
    
    print("=" * 76)
    print(textwrap.fill(kb['judul'].upper(), width=76))
    print("=" * 76)
    print("Jawab setiap pertanyaan dengan 'y' (Ya) atau 't' (Tidak).\n")
    
    fakta_awal = []
    
    if len(sys.argv) > 1 and sys.argv[1].startswith("--test="):
        kasus = sys.argv[1].split("=")[1]
        print(f"[MODE PENGUJIAN OTOMATIS: KASUS {kasus}]")
        if kasus == "1":
            jawaban_ya = {
                "batang tanaman berlubang atau pangkal patah",
                "titik tumbuh pucuk daun mati menggulung mengering",
                "tanaman padi masih berada pada fase vegetatif anakan"
            }
        elif kasus == "2":
            jawaban_ya = {
                "rumpun padi menguning kecokelatan mengering melingkar seperti terbakar",
                "terdapat koloni serangga kecil cokelat di pangkal batang",
                "terdapat cairan manis embun jelaga hitam dan populasi serangga padat"
            }
        elif kasus == "3":
            jawaban_ya = {
                "tanaman padi masih berada pada fase vegetatif anakan"
            }
        else:
            print("Kasus tidak dikenal (pilih 1, 2, atau 3).")
            return
            
        for i, f in enumerate(fakta_tanya, 1):
            tanya = format_pertanyaan(f)
            jawab = "y" if f in jawaban_ya else "t"
            print(f"{i:2d}. {tanya} (y/t) > {jawab}")
            if jawab == "y":
                fakta_awal.append(f)
    else:
        for i, f in enumerate(fakta_tanya, 1):
            tanya = format_pertanyaan(f)
            while True:
                jawab = input(f"{i:2d}. {tanya} (y/t) > ").strip().lower()
                if jawab in ['y', 'ya', 't', 'tidak']:
                    break
                print("   Mohon masukkan 'y' atau 't'.")
            if jawab in ['y', 'ya']:
                fakta_awal.append(f)
                
    print("\n" + "-" * 70)
    print("PROSES INFERENSI FORWARD CHAINING:")
    print("-" * 70)
    print(f"Fakta awal dari pengamatan lapangan ({len(fakta_awal)} gejala/kondisi):")
    if fakta_awal:
        for f in fakta_awal:
            print(f"  * {f}")
    else:
        print("  (Tidak ada gejala yang teridentifikasi)")
    print()
    
    kesimpulan, jejak_alasan, siklus_log = jalankan_forward_chaining(kb, fakta_awal)
    
    for log in siklus_log:
        print(log)
    print()
    
    print("=" * 70)
    print("HASIL DIAGNOSIS & REKOMENDASI PENGENDALIAN:")
    print("=" * 70)
    if kesimpulan:
        for i, k in enumerate(kesimpulan, 1):
            print(f"{i}. {k}")
    else:
        print("Tidak ada diagnosis hama atau penyakit utama yang terdeteksi.")
        print("Gejala fisik yang dimasukkan tidak memenuhi kriteria serangan hama/penyakit utama.")
        
    print("\n" + "-" * 70)
    print("ALASAN PENELUSURAN ATURAN (EXPLANATION TRACE):")
    print("-" * 70)
    if kesimpulan:
        for k in kesimpulan:
            cetak_alasan_rekursif(k, jejak_alasan)
    else:
        print("Tidak ada rantai aturan yang aktif menghasilkan diagnosis.")
        
    print("\n" + "=" * 70)
    print("CATATAN BATAS KEBERLAKUAN (DISCLAIMER):")
    print("=" * 70)
    print(kb["batas"])
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
