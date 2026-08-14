# ==========================================
# ANA EKRAN — KAYNAK KÜTÜPHANESİ
# ==========================================
st.subheader("📚 Kaynak Kütüphanesi")
st.caption(
    "Diskteki `kaynak_kutuphane/` klasöründen yüklenen ders kitabı, makale veya arşiv belgeleri. "
    "Sorular öncelikle buradaki metinlere dayandırılır."
)

with st.expander("📁 Kaynak Dosyaları Yönet & Önizle", expanded=False):
    kutuphane_dosyalari = st.file_uploader(
        "Kütüphaneye yeni PDF/TXT belgeleri ekleyin:",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="Yüklenen dosyalar yerel klasöre kaydedilir ve sonraki oturumlarda da kullanılır."
    )
    
    if kutuphane_dosyalari:
        with st.spinner("Dosyalar kütüphaneye kaydediliyor..."):
            yuklenen_dosyalari_isle(kutuphane_dosyalari)
            metin, adlar = kutuphaneyi_diskten_yukle()
            st.session_state.kaynak_metin = metin
            st.session_state.kaynak_dosya_adlari = adlar
            st.success(f"{len(kutuphane_dosyalari)} yeni dosya kütüphaneye eklendi!")
            st.rerun()

    if st.session_state.get("kaynak_dosya_adlari"):
        st.markdown("**Aktif Kütüphane İçeriği:**")
        for ad in st.session_state.kaynak_dosya_adlari:
            st.markdown(f" - 📄 `{ad}`")
            
        maks_karakter = st.number_input(
            "Model Gönderim Karakter Limiti:",
            min_value=10000,
            max_value=500000,
            value=MAKS_KAYNAK_KARAKTER_VARSAYILAN,
            step=10000,
            help="Çok büyük belgelerde token kotasını aşmamak için metni kırpar."
        )
        
        aktif_metin = st.session_state.kaynak_metin[:maks_karakter]
        if len(st.session_state.kaynak_metin) > maks_karakter:
            st.info(f"⚠️ Kaynak metni toplam {len(st.session_state.kaynak_metin)} karakter. İlk {maks_karakter} karakter modele aktarılacak.")
            
        with st.popover("📖 Birleştirilmiş Metin Önizlemesi"):
            st.text_area("Yüklü Metin İçeriği", value=aktif_metin, height=300, disabled=True)
    else:
        st.info("Kütüphanede henüz dosya yok. Dilerseniz yukarıdan PDF veya TXT belgeleri yükleyebilirsiniz.")
        aktif_metin = ""

st.divider()

# ==========================================
# ÜRETİM BUTONU VE YÖNETİMİ
# ==========================================
uretim_baslat = st.button("🚀 Soru Setini Üret", type="primary", use_container_width=True)

if uretim_baslat:
    if not surec_secimi:
        st.error("Lütfen en az bir süreç bileşeni (alt başlık) seçin.")
    elif not api_key:
        st.error(f"Lütfen geçerli bir {saglayici} API anahtarı girin.")
    else:
        durum_kutusu = st.empty()
        ilerleme_bar = st.progress(0)
        
        def ilerleme_guncelle(mesaj):
            durum_kutusu.info(f"⏳ {mesaj}")

        try:
            ilerleme_guncelle("Prompt hazırlanıyor ve istek oluşturuluyor...")
            
            temel_p = {
                "unite": unite_secimi,
                "cikti_kod": cikti_kod,
                "cikti_tam": cikti_tam,
                "surec_metinleri": surec_secimi,
                "soru_kategorisi": soru_kategorisi,
                "zorluk": zorluk,
                "kaynak_metin": aktif_metin,
                "ek_baglam": ek_baglam
            }
            
            ilerleme_bar.progress(30)
            
            ham_yanit = uret_otomatik_parcali(
                saglayici=saglayici,
                api_key=api_key,
                model=model_secimi,
                temel_parametreler=temel_p,
                toplam_soru=soru_sayisi,
                ilerleme=ilerleme_guncelle
            )
            
            ilerleme_bar.progress(100)
            durum_kutusu.empty()
            ilerleme_bar.empty()
            
            # Üretim sonuçlarını oturum durumuna kaydet
            st.session_state.uretilen_soru = ham_yanit
            st.session_state.son_uretim_meta = {
                "unite": unite_secimi,
                "cikti_kod": cikti_kod,
                "cikti_tam": cikti_tam,
                "surecler": surec_secimi,
                "soru_kategorisi": soru_kategorisi,
                "zorluk": zorluk,
                "soru_sayisi": soru_sayisi,
                "model": f"{saglayici} ({model_secimi})",
                "zaman": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.success("✨ Sorular başarıyla üretildi!")
            
        except Exception as e:
            durum_kutusu.empty()
            ilerleme_bar.empty()
            st.error(f"Üretim sırasında bir hata oluştu: {e}")

# ==========================================
# ANA EKRAN — SEKMELER (ÇIKTI VE HAVUZ)
# ==========================================
tab_uretim, tab_havuz = st.tabs(["📝 Üretilen Sorular", "🗄️ Soru Havuzu ve Dışa Aktarma"])

# ------------------------------------------
# SEKME 1: ÜRETİLEN SORULAR
# ------------------------------------------
with tab_uretim:
    if st.session_state.uretilen_soru:
        meta = st.session_state.son_uretim_meta
        
        st.markdown(f"### 📋 Üretim Detayları")
        st.caption(
            f"**Kategori:** {meta['soru_kategorisi']} | **Zorluk:** {meta['zorluk']} | "
            f"**Soru Sayısı:** {meta['soru_sayisi']} | **Model:** {meta['model']} | **Tarih:** {meta['zaman']}"
        )
        
        # Word olarak indirme ve Havuza Kaydetme butonları
        c1, c2 = st.columns([1, 1])
        with c1:
            if DOCX_MEVCUT:
                word_tampon = ham_metin_word(
                    markdown_metin=st.session_state.uretilen_soru,
                    ust_bilgi=f"Ünite: {meta['unite']} | Çıktı: {meta['cikti_kod']} | Zorluk: {meta['zorluk']}"
                )
                st.download_button(
                    label="📄 Word (.docx) Olarak İndir",
                    data=word_tampon,
                    file_name=f"TYMM_Tarih_11_{meta['cikti_kod']}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        with c2:
            if st.button("📥 Soru Havuzuna Kaydet", use_container_width=True):
                kayit_id = f"{meta['cikti_kod']}_{int(time.time())}"
                yeni_kayit = {
                    "id": kayit_id,
                    "unite": meta["unite"],
                    "cikti_kod": meta["cikti_kod"],
                    "cikti_tam": meta["cikti_tam"],
                    "surecler": meta["surecler"],
                    "soru_kategorisi": meta["soru_kategorisi"],
                    "zorluk": meta["zorluk"],
                    "soru_sayisi": meta["soru_sayisi"],
                    "model": meta["model"],
                    "zaman": meta["zaman"],
                    "icerik": st.session_state.uretilen_soru
                }
                havuza_kaydet(yeni_kayit)
                st.success("Soru seti başarıyla kalıcı havuza kaydedildi!")

        st.divider()
        st.markdown(st.session_state.uretilen_soru)
    else:
        st.info("Henüz soru üretilmedi. Sol panelden parametreleri seçip **Soru Setini Üret** butonuna basın.")

# ------------------------------------------
# SEKME 2: SORU HAVUZU VE DIŞA AKTARMA
# ------------------------------------------
with tab_havuz:
    havuz_verisi = havuzu_yukle()
    
    if not havuz_verisi:
        st.info("Soru havuzu şu anda boş. Ürettiğiniz soru setlerini **Soru Havuzuna Kaydet** butonunu kullanarak buraya aktarabilirsiniz.")
    else:
        st.markdown(f"### 🗄️ Havuzdaki Soru Setleri ({len(havuz_verisi)} Kayıt)")
        
        # Tüm Havuzu Toplu Word Olarak İndir
        if DOCX_MEVCUT:
            toplu_word = coklu_kayit_word(havuz_verisi)
            st.download_button(
                label="📦 Tüm Havuzu Tek Word Belgesi Olarak İndir (.docx)",
                data=toplu_word,
                file_name=f"TYMM_11_Tarih_Soru_Havuzu_Tumu_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
        st.divider()
        
        # Havuzdaki kayıtları listeleme ve yönetme
        for idx, kayit in enumerate(havuz_verisi):
            baslik = (
                f"[{kayit.get('cikti_kod')}] {kayit.get('soru_kategorisi')} — "
                f"{kayit.get('zorluk')} ({kayit.get('soru_sayisi')} Soru) — {kayit.get('zaman')}"
            )
            
            with st.expander(baslik, expanded=False):
                st.markdown(f"**Ünite:** {kayit.get('unite')}")
                st.markdown(f"**Öğrenme Çıktısı:** {kayit.get('cikti_tam')}")
                if kayit.get("surecler"):
                    st.markdown("**Süreç Bileşenleri:** " + ", ".join(kayit["surecler"]))
                st.caption(f"Model: {kayit.get('model')} | Kayıt ID: `{kayit.get('id')}`")
                
                col_h1, col_h2 = st.columns([1, 1])
                
                with col_h1:
                    if DOCX_MEVCUT:
                        tekli_word = tek_kayit_word(kayit)
                        st.download_button(
                            label="📄 Bu Kaydı Word Olarak İndir",
                            data=tekli_word,
                            file_name=f"Soru_{kayit.get('cikti_kod')}_{kayit.get('id')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_{kayit.get('id')}",
                            use_container_width=True
                        )
                
                with col_h2:
                    if st.button("🗑️ Kaydı Havuzdan Sil", key=f"del_{kayit.get('id')}", use_container_width=True):
                        havuzdan_sil(kayit.get("id"))
                        st.warning("Kayıt silindi.")
                        st.rerun()

                st.divider()
                st.markdown(kayit.get("icerik", ""))
