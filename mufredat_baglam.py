# -*- coding: utf-8 -*-
"""11. Sınıf Tarih öğretim programından çıkarılan BAĞLAM ZENGİNLİĞİ verisi.

Kaynak: TYMM 11. Sınıf Tarih 1., 2. ve 3. ünite öğretim programı PDF'leri.
Bu veri, mufredat_verisi.py'deki iskeleti (ünite/çıktı/süreç/soru sayısı) TAMAMLAR.
Amaç: modelin soyut/tekrarlı sorular yerine, programın öngördüğü SOMUT tarihsel
olay, kişi ve kavramlara dayalı, birbirinden farklı sorular üretmesini sağlamak.

Yapı:
UNITE_BAGLAM[ünite adı] = {
    "anahtar_kavramlar": [...],       # ünite geneli
    "alan_becerileri": [...],         # ünite geneli
    "degerler": [...],
    "icerik_cercevesi": [...],        # ünite geneli başlıklar
}
CIKTI_BAGLAM[çıktı kodu] = {
    "olcumlenen_beceri": "...",       # bu çıktının merkezî bilişsel becerisi
    "somut_icerik": [...],            # bu çıktı işlenirken kullanılacak somut olay/kişi/antlaşma
}
"""

# ==========================================
# ÜNİTE DÜZEYİ BAĞLAM
# ==========================================
UNITE_BAGLAM = {
    "1. ÜNİTE : DEĞİŞEN DÜNYADA OSMANLI DEVLETİ (1683-1789)": {
        "anahtar_kavramlar": ["barok", "devrim", "hendesehane", "matbaa", "rokoko", "sanayileşme", "sefaret"],
        "alan_becerileri": [
            "SBAB1. Zamanı Algılama ve Kronolojik Düşünme",
            "SBAB2. Kanıta Dayalı Sorgulama ve Araştırma (Kaynağı Yorumlama)",
            "SBAB4. Değişim ve Sürekliliği Neden ve Sonuçlarıyla Yorumlama",
            "KB2.7. Karşılaştırma",
        ],
        "degerler": ["D5. Duyarlılık", "D7. Estetik", "D17. Tasarruf", "D18. Temizlik"],
        "icerik_cercevesi": [
            "Osmanlı Devleti’nin 1683-1789 Yılları Arasındaki Siyasi ve Askerî Mücadeleleri",
            "Lale Devri’nin Devlet ve Toplum Hayatına Etkileri",
            "1755 Lizbon ve 1766 İstanbul Depremlerinin Etkileri",
            "Sanayi Devrimi’nin Meydana Getirdiği Siyasi, Sosyal ve Ekonomik Değişim",
        ],
    },
    "2. ÜNİTE : DÖNÜŞÜM SÜRECİNDE OSMANLI (1789-1908)": {
        "anahtar_kavramlar": ["azınlık", "cumhuriyetçilik", "ihtilal", "kapitalizm", "komünizm",
                              "liberalizm", "meşrutiyet", "milliyetçilik", "panslavizm", "sosyalizm"],
        "alan_becerileri": [
            "SBAB4. Değişim ve Sürekliliği Neden ve Sonuçlarıyla Yorumlama",
            "SBAB2. Kanıta Dayalı Sorgulama ve Araştırma (Kaynağı Yorumlama)",
            "SBAB17. Tarihsel Sorun Analizi ve Karar Verme",
            "KB2.8. Sorgulama", "KB3.3. Eleştirel Düşünme",
        ],
        "degerler": ["D1. Adalet", "D3. Çalışkanlık", "D11. Özgürlük"],
        "icerik_cercevesi": [
            "Fransız İhtilali’nin Devlet ve Toplum Hayatında Meydana Getirdiği Değişim",
            "1789-1908 Yılları Arasında Osmanlı Devleti’nde Meydana Gelen Siyasi, Askerî ve İdari Gelişmeler",
            "1789-1908 Yılları Arasında Osmanlı Devleti’nde Bilim, Sanat ve Teknoloji Alanlarında Gelişmeler",
            "Osmanlı Devleti’nde Sanayileşme Çabaları",
        ],
    },
    "3. ÜNİTE : SAVAŞLAR SARMALINDA OSMANLI (1908- 1918)": {
        "anahtar_kavramlar": ["bloklaşma", "darbe", "fırka", "göç", "komita", "muhacir", "mütareke", "müttefik", "salgın"],
        "alan_becerileri": [
            "SBAB3. Tarihsel Empati (Tarihsel Bağlamsallaştırma)",
            "SBAB2. Kanıta Dayalı Sorgulama ve Araştırma",
            "KB2.7. Karşılaştırma", "KB3.1. Karar Verme", "KB3.2. Problem Çözme",
        ],
        "degerler": ["D9. Merhamet", "D16. Sorumluluk", "D19. Vatanseverlik"],
        "icerik_cercevesi": [
            "1908-1918 Yılları Arasında Osmanlı Devleti’nde Meydana Gelen Siyasi ve Askerî Gelişmeler",
            "1908-1918 Yılları Arasında Gerçekleşen Kitlesel Göç ve Salgınlar",
            "Osmanlı Devleti’nin İnsanlık Tarihine Katkıları",
        ],
    },
}

# ==========================================
# ÇIKTI DÜZEYİ BAĞLAM (en kritik katman)
# "somut_icerik": programın "Öğrenme-Öğretme Uygulamaları" bölümünde
# o çıktı için açıkça adı geçen olay, antlaşma, kişi ve olguları içerir.
# ==========================================
CIKTI_BAGLAM = {
    # ---------- 1. ÜNİTE ----------
    "TAR.11.1.1": {
        "olcumlenen_beceri": "Siyasi ve askerî mücadelelerin sonuçlarını karşılaştırma ve bunlara ilişkin yargıda bulunma",
        "somut_icerik": [
            "II. Viyana Kuşatması", "Karlofça Antlaşması", "Prut Antlaşması",
            "Pasarofça Antlaşması", "Belgrad Antlaşması", "Küçük Kaynarca Antlaşması",
            "bu antlaşmaların Osmanlı’ya siyasi ve askerî açıdan güç kaybettirme dereceleri",
        ],
    },
    "TAR.11.1.2": {
        "olcumlenen_beceri": "Lale Devri’ndeki değişimi tarihsel bağlamı içinde kaynaklara dayanarak yorumlama, tablolaştırma ve açıklama",
        "somut_icerik": [
            "Lale Devri’nde toplumsal, kültürel ve sanatsal değişim", "mimari ve diplomaside değişim",
            "sefaret (elçilik) faaliyetleri", "matbaanın gelişi (İbrahim Müteferrika)",
            "barok ve rokoko sanat üslupları", "Şair Nedim", "israf ve dönemin eserlerinin estetik değeri",
        ],
    },
    "TAR.11.1.3": {
        "olcumlenen_beceri": "1755 Lizbon ve 1766 İstanbul depremlerini etkileri bakımından karşılaştırma (benzerlik ve farklılık listeleme)",
        "somut_icerik": [
            "1755 Lizbon depremi", "1766 İstanbul depremi",
            "depremlerin idari etkileri", "sosyal etkileri", "ekonomik etkileri",
            "afet bilincinin önemi", "iki depremin benzerlik ve farklılıkları",
        ],
    },
    "TAR.11.1.4": {
        "olcumlenen_beceri": "Sanayi Devrimi’nin siyasi, sosyal, ekonomik değişimini neden ve sonuçlarıyla yorumlama (olumlu/olumsuz sorgulama)",
        "somut_icerik": [
            "Sanayi Devrimi’nin nedenleri", "sömürgecilik", "Rönesans ve Reform’un etkisi",
            "siyasi, sosyal ve ekonomik sonuçlar", "çevre kirliliği", "makine kırıcılığı",
            "düzensiz kentleşme", "olumlu ve olumsuz etkiler",
        ],
    },
    # ---------- 2. ÜNİTE ----------
    "TAR.11.2.1": {
        "olcumlenen_beceri": "Fransız İhtilali’nin devlet ve toplum hayatındaki değişimini neden ve sonuçlarıyla yorumlama",
        "somut_icerik": [
            "Bilim Devrimi", "Aydınlanma düşüncesi", "Amerika’nın bağımsızlık mücadelesi",
            "insan hakları, eşitlik, adalet, milliyetçilik, özgürlük kavramları",
            "ihtilalin yerel, bölgesel ve küresel etkileri", "olumlu ve olumsuz yönleri",
        ],
    },
    "TAR.11.2.2": {
        "olcumlenen_beceri": "1789-1908 siyasi, askerî, idari gelişmelerin Osmanlı yönetim ve toplum yapısına etkilerini sorgulama ve çıkarım yapma",
        "somut_icerik": [
            "Şark Meselesi", "Sırp İsyanı", "Yunan İsyanı", "Mısır Meselesi", "Boğazlar Meselesi",
            "Tanzimat Fermanı", "Kırım Harbi", "Islahat Fermanı", "Kanun-ı Esasi",
            "93 Harbi ve Anadolu’ya göçler", "Düyûn-ı Umûmiyye",
            "II. Abdülhamid’in siyonist faaliyetlere karşı tutumu",
        ],
    },
    "TAR.11.2.3": {
        "olcumlenen_beceri": "1789-1908 Osmanlı’da bilim, sanat ve teknoloji uygulamalarını yorumlama ve işlevselliğini açıklama",
        "somut_icerik": [
            "demir yolu", "fotoğraf makinesi", "telgraf",
            "bu teknolojilerin Osmanlı’da kullanımında yaşanan zorluklar ve aşılması",
            "bilim, sanat ve teknoloji uygulamalarının işlevselliği", "azim ve gayretin önemi",
        ],
    },
    "TAR.11.2.4": {
        "olcumlenen_beceri": "Osmanlı’nın sanayileşmede geri kalma sorununa tarafların bakışını çözümleme, karşılaştırma ve alternatif çözüm üretme (Tarihsel Sorun Analizi)",
        "somut_icerik": [
            "Osmanlı’nın sanayileşmede geri kalma sorunu", "Rusya’nın sanayileşme hamlesi",
            "Japonya’nın sanayileşme hamlesi (karşılaştırma örnekleri)",
            "cesaret ve girişimciliğin ekonomiye katkısı", "alternatif çözüm önerileri ve olası sonuçları",
        ],
    },
    # ---------- 3. ÜNİTE ----------
    "TAR.11.3.1": {
        "olcumlenen_beceri": "1908-1918 siyasi ve askerî gelişmelerin sonuçlarını tarihsel bağlamı içinde değerlendirme",
        "somut_icerik": [
            "II. Meşrutiyet’in ilanı", "31 Mart Olayı", "Bâbıâli Baskını",
            "Trablusgarp Savaşı", "Balkan Savaşları", "I. Dünya Savaşı süreci", "Sevk ve İskân Kanunu",
            "Sarıkamış Harekâtı", "Çanakkale Zaferi", "Kûtülamâre Zaferi",
            "Medine Müdafaası", "Kafkas İslam Ordusu’nun Bakü’yü kurtarması",
            "Adalar (Ege) Denizi ve Batı Trakya sorunlarının başlangıcı", "asılsız Ermeni iddialarının başlangıcı",
        ],
    },
    "TAR.11.3.2": {
        "olcumlenen_beceri": "1908-1918 kitlesel göç ve salgınların devlet ve toplum hayatına etkilerine tarihsel empatiyle bakış açısı geliştirme ve karşılaştırma",
        "somut_icerik": [
            "Balkan Savaşları ve I. Dünya Savaşı sürecinde Anadolu’ya kitlesel göçler",
            "kolera, sıtma ve tifüs salgınları", "muhacirlerin göç hikâyeleri ve yaşadıkları zorluklar",
            "dönemin sınırlı sağlık imkânları (hastane, personel, bilimsel gelişme)",
            "salgınların ordu, halk ve devlete etkileri", "yardımlaşma ve dayanışmanın önemi",
            "geçmiş ve günümüz göç/salgınlarının karşılaştırılması",
        ],
    },
    "TAR.11.3.3": {
        "olcumlenen_beceri": "Osmanlı’nın insanlık tarihine katkılarına ilişkin kaynak toplama, sorgulama ve kanıta dayalı özgün ürün oluşturma",
        "somut_icerik": [
            "Osmanlı’nın askerî, siyasi, sosyal, ekonomik ve kültürel alanlardaki katkıları",
            "kaynak türü, yazarı, tarihi, güvenilirliği (kaynak sorgulama)",
            "olgu ve görüş ayrımı", "kaynaklardaki farklı görüşlerin karşılaştırılması",
            "Osmanlı kültürel mirası ve korunmasının önemi",
        ],
    },
}
