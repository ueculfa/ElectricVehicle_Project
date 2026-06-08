import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Global EV Şarj Ağı STGCN Paneli", layout="wide", page_icon="🌍")

st.title("🌍 15 Ülkelik Elektrikli Araç Şarj Ağı Dinamik STGCN Simülasyonu")
st.markdown("Avrupa ve Türkiye'deki şarj istasyonlarının Çok Dilli Yapay Zeka (NLP) Duygu Analizi ve Dinamik Yönlendirme Kıyaslaması.")
st.markdown("---")

@st.cache_data
def veri_yukle():
    all_data = []

    # 1. Eski formatlı dosyaları yükleme
    eski_dosyalar = [
        ("Türkiye", "Koridor_NLP_Analizli.csv", "Kritik_Koridor_Istasyonlari.csv"),
        ("Almanya", "Koridor_Almanya_NLP_Analizli.csv", "Kritik_Koridor_Almanya.csv"),
        ("Hollanda", "Koridor_Hollanda_NLP_Analizli.csv", "Kritik_Koridor_Hollanda.csv")
    ]
    
    # Olası Priz (Soket) kolonu isimleri
    olasi_priz_isimleri = ['NumberOfPoints', 'Connections', 'Priz_Sayisi', 'Kapasite', 'Soket_Sayisi']

    for ulke, nlp_file, koor_file in eski_dosyalar:
        if os.path.exists(nlp_file) and os.path.exists(koor_file):
            df_nlp = pd.read_csv(nlp_file)
            df_koor = pd.read_csv(koor_file)
            
            priz_kolonu = 'Priz_Sayisi'
            df_koor[priz_kolonu] = 1 
            for col in olasi_priz_isimleri:
                if col in df_koor.columns:
                    df_koor[priz_kolonu] = df_koor[col].fillna(1)
                    break
            
            cols_to_add = ['OCM_ID']
            for col in ['Enlem', 'Boylam', 'Operator', 'Istasyon_Adi', 'Priz_Sayisi']:
                if col not in df_nlp.columns and col in df_koor.columns:
                    cols_to_add.append(col)
            
            if len(cols_to_add) > 1:
                df_nlp = pd.merge(df_nlp, df_koor[cols_to_add], on='OCM_ID', how='left')
            
            for col in ['Enlem', 'Boylam']:
                if col not in df_nlp.columns: df_nlp[col] = 0.0
            for col in ['Operator', 'Istasyon_Adi']:
                if col not in df_nlp.columns: df_nlp[col] = 'Bilinmeyen Marka'
            if 'Priz_Sayisi' not in df_nlp.columns: df_nlp['Priz_Sayisi'] = 1

            df_nlp['Ulke'] = ulke
            
            istasyon_skor = df_nlp.groupby(['OCM_ID', 'Enlem', 'Boylam', 'Operator', 'Istasyon_Adi', 'Priz_Sayisi'])['Tutum_Skoru'].mean().reset_index()
            istasyon_skor['Ulke'] = ulke
            
            all_data.append((istasyon_skor, df_nlp))

    # 2. Yeni dosyalar
    yeni_dosyalar = glob.glob("Final_NLP_*.csv")
    for file in yeni_dosyalar:
        df_nlp = pd.read_csv(file)
        if not df_nlp.empty:
            ulke_adi = file.replace("Final_NLP_", "").replace(".csv", "")
            
            if 'Priz_Sayisi' not in df_nlp.columns:
                df_nlp['Priz_Sayisi'] = 1
                for col in olasi_priz_isimleri:
                    if col in df_nlp.columns:
                        df_nlp['Priz_Sayisi'] = df_nlp[col].fillna(1)
                        break
            
            for col in ['Enlem', 'Boylam']:
                if col not in df_nlp.columns: df_nlp[col] = 0.0
            for col in ['Operator', 'Istasyon_Adi']:
                if col not in df_nlp.columns: df_nlp[col] = 'Bilinmeyen Marka'
                
            istasyon_skor = df_nlp.groupby(['OCM_ID', 'Enlem', 'Boylam', 'Operator', 'Istasyon_Adi', 'Priz_Sayisi'])['Tutum_Skoru'].mean().reset_index()
            istasyon_skor['Ulke'] = ulke_adi
            df_nlp['Ulke'] = ulke_adi
            
            all_data.append((istasyon_skor, df_nlp))

    if not all_data:
        return pd.DataFrame(), pd.DataFrame()

    df_harita = pd.concat([item[0] for item in all_data], ignore_index=True)
    df_nlp_master = pd.concat([item[1] for item in all_data], ignore_index=True)
    
    def skor_etiket(val):
        if val > 0: return "Olumlu"
        elif val < 0: return "Olumsuz"
        return "Nötr"
    df_nlp_master['Tutum_Etiketi_Guvenli'] = df_nlp_master['Tutum_Skoru'].apply(skor_etiket)
    
    return df_harita, df_nlp_master

# Veriyi Çağır
df_harita, df_nlp = veri_yukle()

if not df_harita.empty:
    
    # --- DİNAMİK KONTROL PANELİ ---
    st.sidebar.header("⚙️ NLP-STGCN Dinamik Simülasyonu")
    st.sidebar.markdown("Yapay zekanın ağ trafiğine nasıl müdahale edeceğini belirleyin.")
    
    esik_deger = st.sidebar.slider(
        "NLP Tolerans Eşiği (Minimum Skor)", 
        min_value=-1.0, 
        max_value=0.5, 
        value=-0.2, 
        step=0.1,
        help="Bu skorun altında kalan (şikayet alan) istasyonlar NLP modelimiz tarafından riskli kabul edilip ağdan 'İzole' edilecektir."
    )
    
    df_aktif = df_harita[df_harita['Tutum_Skoru'] >= esik_deger].copy()
    df_izole = df_harita[df_harita['Tutum_Skoru'] < esik_deger].copy()
    df_nlp_aktif = df_nlp[df_nlp['OCM_ID'].isin(df_aktif['OCM_ID'])].copy()
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"🟢 **Aktif İstasyon (Ağda):** {len(df_aktif)}\n\n⚫ **İzole İstasyon (Koparılan):** {len(df_izole)}")

    # --- KPI METRİKLERİ ---
    st.subheader("📌 Genel Veri ve Simülasyon Özeti")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Toplam İstasyon", f"{len(df_harita):,}")
    col2.metric("Toplam Çekilen Yorum", f"{len(df_nlp):,}") 
    col3.metric("Aktif (Güvenli) İstasyon", f"{len(df_aktif):,}")
    col4.metric("İzole (Riskli) İstasyon", f"{len(df_izole):,}")
    col5.metric("Kalan Aktif Yorum", f"{len(df_nlp_aktif):,}")

    st.markdown("---")
    
    # --- İNTERAKTİF STGCN GRAF HARİTASI ---
    st.markdown("### 🗺️ Uluslararası Şarj STGCN Graf Haritası (Gerçek Otoyol Ağı)")
    
    merkez_enlem = df_harita['Enlem'].mean()
    merkez_boylam = df_harita['Boylam'].mean()

    fig_map = go.Figure()

    rota_dosyasi = "Gercek_Otoyol_Rotalari.csv"
    if os.path.exists(rota_dosyasi):
        df_rotalar = pd.read_csv(rota_dosyasi)
        fig_map.add_trace(go.Scattermapbox(
            lat=df_rotalar['Enlem'], lon=df_rotalar['Boylam'], mode='lines',
            line=dict(width=1.5, color='rgba(100, 100, 100, 0.4)'),
            hoverinfo='none', name="Fiziksel Otoyol Altyapısı (Edges)"
        ))

    # --- İZOLE EDİLEN DÜĞÜMLER HOVER BİLGİSİ ---
    if not df_izole.empty:
        hover_metin_izole = (
            "<b>" + df_izole["Istasyon_Adi"] + "</b><br>" +
            "🌍 Ülke: " + df_izole["Ulke"] + "<br>" +
            "🏢 Marka: " + df_izole["Operator"] + "<br>" +
            "🔌 Priz Sayısı: " + df_izole["Priz_Sayisi"].astype(int).astype(str) + "<br>" +
            "⚠️ Durum: İZOLE EDİLDİ (Riskli Skor)"
        )
        
        fig_map.add_trace(go.Scattermapbox(
            lat=df_izole["Enlem"], lon=df_izole["Boylam"],
            mode='markers',
            marker=go.scattermapbox.Marker(size=8, color='black', opacity=0.8),
            text=hover_metin_izole,
            hoverinfo='text',
            name="İzole Edilen Düğümler"
        ))

    # --- AKTİF DÜĞÜMLER HOVER BİLGİSİ VE KÜÇÜLTÜLMÜŞ RENK BAR ---
    if not df_aktif.empty:
        hover_metin_aktif = (
            "<b>" + df_aktif["Istasyon_Adi"] + "</b><br>" +
            "🌍 Ülke: " + df_aktif["Ulke"] + "<br>" +
            "🏢 Marka: " + df_aktif["Operator"] + "<br>" +
            "🔌 Priz Sayısı: " + df_aktif["Priz_Sayisi"].astype(int).astype(str) + "<br>" +
            "⭐ NLP Memnuniyet Skoru: " + df_aktif["Tutum_Skoru"].round(2).astype(str)
        )
        
        fig_map.add_trace(go.Scattermapbox(
            lat=df_aktif["Enlem"], lon=df_aktif["Boylam"],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=12,
                color=df_aktif["Tutum_Skoru"],
                colorscale=[[0, "red"], [0.5, "yellow"], [1, "green"]],
                cmin=-1, cmax=1,
                showscale=True,
                colorbar=dict(
                    title="NLP Skoru",
                    thickness=15,    # Renk çubuğunu incelttik
                    len=0.5,         # Boyunu haritanın yarısı kadar yaptık (Başlığa taşmasını engeller)
                    y=0.45,          # Dikey olarak biraz daha aşağı indirdik
                    yanchor="middle"
                )
            ),
            text=hover_metin_aktif,
            hoverinfo='text',
            name="Aktif İstasyonlar (Nodes)"
        ))

    fig_map.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(style="carto-positron", zoom=4, center=dict(lat=merkez_enlem, lon=merkez_boylam)),
        modebar=dict(orientation='v', bgcolor='rgba(0,0,0,0)'), dragmode='zoom',
        height=700
    )
    st.plotly_chart(fig_map, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

    st.markdown("---")

    # --- ÜLKE VE OPERATÖR GRAFİKLERİ ---
    st.markdown("### 📊 Aktif Ağa Göre Ülkelerin Memnuniyet Dağılımı")
    duygu_ozeti = df_nlp_aktif.groupby(['Ulke', 'Tutum_Etiketi_Guvenli']).size().reset_index(name='Sayi')
    if not duygu_ozeti.empty:
        fig_bar = px.bar(
            duygu_ozeti, x="Ulke", y="Sayi", color="Tutum_Etiketi_Guvenli", barmode="stack",
            color_discrete_map={"Olumlu":"#28a745", "Olumsuz":"#dc3545", "Nötr":"#6c757d"},
            category_orders={"Tutum_Etiketi_Guvenli": ["Olumlu", "Nötr", "Olumsuz"]}
        )
        fig_bar.update_layout(xaxis={'categoryorder':'total descending'}, margin={"r":0,"t":30,"l":0,"b":0})
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🏆 Aktif Ağdaki Operatör Performans Kıyaslaması")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ⭐ En Güvenilir Operatörler")
        guvenilir_df = df_nlp_aktif[df_nlp_aktif['Tutum_Skoru'] > 0]
        if not guvenilir_df.empty:
            guvenilir_operatorler = guvenilir_df['Operator'].value_counts().head(10).reset_index()
            guvenilir_operatorler.columns = ['Operator', 'Olumlu Yorum Sayısı']
            fig_pie_pos = px.pie(guvenilir_operatorler, values='Olumlu Yorum Sayısı', names='Operator', hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
            st.plotly_chart(fig_pie_pos, use_container_width=True)
            
    with c2:
        st.markdown("#### ⚠️ Kalan İstasyonlardaki Şikayetler")
        riskli_df = df_nlp_aktif[df_nlp_aktif['Tutum_Skoru'] < 0]
        if not riskli_df.empty:
            riskli_operatorler = riskli_df['Operator'].value_counts().head(10).reset_index()
            riskli_operatorler.columns = ['Operator', 'Şikayet Sayısı']
            fig_pie_neg = px.pie(riskli_operatorler, values='Şikayet Sayısı', names='Operator', hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
            st.plotly_chart(fig_pie_neg, use_container_width=True)
        else:
            st.success("✅ Seçtiğiniz eşik seviyesinde ağdaki tüm şikayet alan istasyonlar başarıyla izole edildi!")

    st.markdown("---")
    st.markdown("### 🎯 Gerçek Kalite: Aktif Ağda Yüzdelik Oranlara Göre Markalar")
    operator_stats = df_nlp_aktif.groupby('Operator').agg(
        Toplam_Yorum=('Tutum_Skoru', 'count'),
        Olumlu_Yorum=('Tutum_Skoru', lambda x: (x > 0).sum()),
        Olumsuz_Yorum=('Tutum_Skoru', lambda x: (x < 0).sum())
    ).reset_index()

    filtreli_operatorler = operator_stats[operator_stats['Toplam_Yorum'] >= 15].copy()
    if not filtreli_operatorler.empty:
        filtreli_operatorler['Başarı Oranı (%)'] = (filtreli_operatorler['Olumlu_Yorum'] / filtreli_operatorler['Toplam_Yorum']) * 100
        filtreli_operatorler['Şikayet Oranı (%)'] = (filtreli_operatorler['Olumsuz_Yorum'] / filtreli_operatorler['Toplam_Yorum']) * 100
        filtreli_operatorler['Iyi_Yazi'] = filtreli_operatorler.apply(lambda r: f"%{r['Başarı Oranı (%)']:.1f} ({int(r['Toplam_Yorum'])} Yorum)", axis=1)
        filtreli_operatorler['Kotu_Yazi'] = filtreli_operatorler.apply(lambda r: f"%{r['Şikayet Oranı (%)']:.1f} ({int(r['Toplam_Yorum'])} Yorum)", axis=1)

        col_oran1, col_oran2 = st.columns(2)
        with col_oran1:
            en_iyi_5 = filtreli_operatorler.sort_values(by='Başarı Oranı (%)', ascending=False).head(5)
            fig_iyi = px.bar(en_iyi_5, x="Başarı Oranı (%)", y="Operator", orientation='h', text="Iyi_Yazi", color="Başarı Oranı (%)", color_continuous_scale="Greens")
            fig_iyi.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_range=[0, 100], showlegend=False, height=400)
            st.plotly_chart(fig_iyi, use_container_width=True)

        with col_oran2:
            en_kotu_5 = filtreli_operatorler.sort_values(by='Şikayet Oranı (%)', ascending=False).head(5)
            fig_kotu = px.bar(en_kotu_5, x="Şikayet Oranı (%)", y="Operator", orientation='h', text="Kotu_Yazi", color="Şikayet Oranı (%)", color_continuous_scale="Reds")
            fig_kotu.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_range=[0, 100], showlegend=False, height=400)
            st.plotly_chart(fig_kotu, use_container_width=True)

    # --- KAPASİTE (PRİZ SAYISI) VS MEMNUNİYET ANALİZİ ---
    st.markdown("---")
    st.markdown("### 🔌 Makale İspatı: İstasyon Kapasitesi (Priz Sayısı) ve Verimlilik Korelasyonu")
    st.markdown("*Bu analiz, istasyonlardaki priz sayısı (fiziksel kapasite) ile yapay zeka tarafından ölçülen NLP müşteri memnuniyeti arasındaki ilişkiyi gösterir.*")
    
    df_priz_analiz = df_aktif[(df_aktif['Priz_Sayisi'] > 0) & (df_aktif['Priz_Sayisi'] < 30)].copy()
    if not df_priz_analiz.empty:
        fig_priz = px.box(
            df_priz_analiz, x="Priz_Sayisi", y="Tutum_Skoru", points="all", 
            hover_name="Istasyon_Adi", hover_data=["Operator", "Ulke"],
            labels={"Priz_Sayisi": "Fiziksel Kapasite (Priz/Soket Sayısı)", "Tutum_Skoru": "NLP Memnuniyet Skoru"},
            color_discrete_sequence=["#2E86C1"]
        )
        fig_priz.update_layout(height=500, xaxis=dict(dtick=1)) 
        st.plotly_chart(fig_priz, use_container_width=True)

    # --- HACİM VS VERİMLİLİK KORELASYON ANALİZİ ---
    st.markdown("---")
    st.markdown("### 📈 Makale İspatı: Aktif Ağda Hacim ve Verimlilik Korelasyonu")
    istasyon_istatistik = df_nlp_aktif.groupby(['OCM_ID', 'Istasyon_Adi', 'Operator', 'Ulke']).agg(
        Yorum_Sayisi=('Tutum_Skoru', 'count'),
        Ortalama_Skor=('Tutum_Skoru', 'mean')
    ).reset_index()

    istasyon_istatistik = istasyon_istatistik[istasyon_istatistik['Yorum_Sayisi'] >= 5]
    if not istasyon_istatistik.empty:
        mevcut_ulkeler = sorted(istasyon_istatistik['Ulke'].unique().tolist())
        secilen_ulkeler = st.multiselect("🌍 Korelasyon Analizi İçin Ülke Seçimi:", options=mevcut_ulkeler, default=mevcut_ulkeler)
        filtrelenmis_veri = istasyon_istatistik[istasyon_istatistik['Ulke'].isin(secilen_ulkeler)]
        if not filtrelenmis_veri.empty:
            try:
                fig_scatter = px.scatter(
                    filtrelenmis_veri, x="Yorum_Sayisi", y="Ortalama_Skor", 
                    color="Ulke", hover_name="Istasyon_Adi", hover_data=["Operator"],
                    trendline="ols", trendline_scope="overall",
                    labels={"Yorum_Sayisi": "İstasyon Hacmi (Toplam Yorum Sayısı)", "Ortalama_Skor": "Verimlilik (Ort. NLP Skoru)"},
                    opacity=0.7
                )
                fig_scatter.update_layout(yaxis_range=[-1.1, 1.1], height=500)
                st.plotly_chart(fig_scatter, use_container_width=True)
            except Exception as e:
                st.warning("Trend çizgisi çizilemedi.")
    
else:
    st.error("Veriler birleştirilemedi. CSV dosyalarının klasörde olduğundan emin ol.")