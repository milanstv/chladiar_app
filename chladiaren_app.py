import streamlit as st
import pandas as pd
from typing import Dict, Tuple, List, Union

# ... (KÓD ZÁKLADNÉHO VÝPOČTU CHLADIACEHO VÝKONU ostáva nezmenený) ...
# ... chladiaci_vykon() a odporucane_hodnoty() ...

# ==========================================
# NOVÁ SEKCIA: KONVERZIA POTRUBIA A CHLADIVÁ
# ==========================================

PIPE_CONVERSION: Dict[str, float] = {
    '1/4"': 6.35,
    '3/8"': 9.52,
    '1/2"': 12.7,
    '5/8"': 15.88,
    '3/4"': 19.05,
    '7/8"': 22.22,
    '1 1/8"': 28.58,
    # Možno by stačili len najbežnejšie priemery
}

COMMON_REFRIGERANTS = {
    "R410A": {
        "Typ": "HFC (Zmes)",
        "GWP": 2088,
        "Poznámka": "Vysoký tlak, nahrádzaný R32.",
    },
    "R32": {
        "Typ": "HFC (Jednozložkové)",
        "GWP": 675,
        "Poznámka": "Nízky GWP, používaný v nových split systémoch.",
    },
    "R404A": {
        "Typ": "HFC (Zmes)",
        "GWP": 3922,
        "Poznámka": "Postupne sa vyraďuje kvôli vysokému GWP.",
    },
    "R134a": {
        "Typ": "HFC (Jednozložkové)",
        "GWP": 1430,
        "Poznámka": "Automobilové klimatizácie, chladiace zariadenia.",
    },
    "R290": {
        "Typ": "HC (Prírodné)",
        "GWP": 3,
        "Poznámka": "Propán. Extrémne nízky GWP, vyžaduje bezpečnostné opatrenia.",
    },
}

# --- Hlavná aplikácia Streamlit ---


def main():
    # ... (KÓD PRED MAIN, FUNKCIE CHLADIACEHO VÝKONU) ...
    # Z dôvodu prehľadnosti Streamlit kódu ponechávam funkcie chladiaci_vykon a odporucane_hodnoty z predchádzajúceho príspevku.

    st.set_page_config(
        page_title="Chladiarenská Kalkulačka | chladiar.sk", layout="wide"
    )
    st.title("🛠️ Nástroje a kalkulácie pre chladiarov")

    # --- TABS: ROZDELENIE APLIKÁCIE NA SEKCIU KALKULÁCIA A NÁSTROJE ---
    tab1, tab2 = st.tabs(["1. Kalkulácia výkonu chladiarne", "2. Prevodník a Chladivá"])

    # ==========================================
    # KARTA 1: KALKULÁCIA VÝKONU
    # ==========================================
    with tab1:
        st.header("Kalkulátor chladiaceho výkonu (Q)")

        # Pôvodné vstupy a výstupy z predchádzajúceho príspevku:
        col1, col2 = st.columns(2)

        # --- Získanie rozmerov ---
        with col1:
            st.subheader("1. Základné parametre")
            dlzka_m = st.number_input(
                "Vnútorná dĺžka chladiarne [m]",
                min_value=1.0,
                value=3.0,
                step=0.1,
                key="dlzka",
            )
            sirka_m = st.number_input(
                "Vnútorná šírka chladiarne [m]",
                min_value=1.0,
                value=3.0,
                step=0.1,
                key="sirka",
            )
            vyska_m = st.number_input(
                "Vnútorná výška chladiarne [m]",
                min_value=1.0,
                value=2.5,
                step=0.1,
                key="vyska",
            )

            objem_m3 = dlzka_m * sirka_m * vyska_m
            plocha_m2 = 2 * (dlzka_m * sirka_m + dlzka_m * vyska_m + sirka_m * vyska_m)

            st.metric(label="Vypočítaný objem", value=f"{objem_m3:.2f} m³")
            st.metric(label="Vypočítaná plocha obálky", value=f"{plocha_m2:.1f} m²")

            st.subheader("Teplotné podmienky a Izolácia")
            vnutorna_teplota = st.number_input(
                "Požadovaná vnútorná teplota [°C]", value=5.0, step=1.0, key="tint"
            )
            vonkajsia_teplota = st.number_input(
                "Maximálna vonkajšia teplota [°C]", value=30.0, step=1.0, key="text"
            )

            panel_options = {
                "PUR 40 mm (U=0.55)": 0.55,
                "PUR 60 mm (U=0.35)": 0.35,
                "PUR 100 mm (U=0.20)": 0.20,
            }
            panel_vyber = st.selectbox(
                "Vyberte typ panelu (U [W/m²·K])",
                options=list(panel_options.keys()),
                index=1,
                key="panel",
            )
            U = panel_options[panel_vyber]

        # --- Tepelné zisky a Výpočet ---
        with col2:
            st.subheader("2. Tepelné zisky")
            vymena_odp, osvetlenie_odp, osoby_tovar_odp = odporucane_hodnoty(objem_m3)

            st.info(
                f"Odporúčané hodnoty: Výmeny: {vymena_odp:.1f} h⁻¹, Osvetlenie: {osvetlenie_odp:.2f} kW, Interné: {osoby_tovar_odp:.2f} kW"
            )

            vymena_vzduchu_za_hod = st.number_input(
                "Počet výmen vzduchu za hodinu [h⁻¹]",
                min_value=0.0,
                value=vymena_odp,
                step=0.1,
                format="%.1f",
                key="vymena",
            )
            osvetlenie_kW = st.number_input(
                "Výkon osvetlenia [kW]",
                min_value=0.0,
                value=osvetlenie_odp,
                step=0.01,
                format="%.2f",
                key="osvetlenie",
            )
            osoby_a_tovar_kW = st.number_input(
                "Ostatné vnútorné zisky [kW]",
                min_value=0.0,
                value=osoby_tovar_odp,
                step=0.01,
                format="%.2f",
                key="zisky",
            )

            st.markdown("---")
            if st.button("Vypočítať", type="primary", key="calc_button"):
                Q_celk, Q_steny, Q_vzduch, Q_vnutorne = chladiaci_vykon(
                    objem_m3,
                    plocha_m2,
                    vnutorna_teplota,
                    vonkajsia_teplota,
                    U,
                    vymena_vzduchu_za_hod,
                    osvetlenie_kW,
                    osoby_a_tovar_kW,
                )

                Q_odporucany = Q_celk * 1.3

                st.subheader("✅ Výsledok")
                st.metric(label="CELKOVÝ VYPOČÍTANÝ VÝKON", value=f"{Q_celk:.2f} kW")
                st.success(
                    f"ODPORÚČANÝ VÝKON JEDNOTKY (s 30 % rezervou): **{Q_odporucany:.2f} kW**"
                )

                st.markdown("**Detailné rozdelenie ziskov:**")
                # Zobrazenie v tabuľke
                df_zisky = pd.DataFrame(
                    {
                        "Zložka zisku": ["Transmisia", "Infiltrácia", "Interné"],
                        "Výkon [kW]": [Q_steny, Q_vzduch, Q_vnutorne],
                        "Podiel [%]": [
                            Q_steny / Q_celk * 100,
                            Q_vzduch / Q_celk * 100,
                            Q_vnutorne / Q_celk * 100,
                        ],
                    }
                )
                st.dataframe(df_zisky, hide_index=True)

    # ==========================================
    # KARTA 2: PREVODNÍK A CHLADIVÁ
    # ==========================================
    with tab2:
        st.header("Rýchle nástroje pre chladiarov")

        st.subheader("Prevod priemeru potrubia (Palce na mm)")

        # Prevodník
        col_pipe1, col_pipe2 = st.columns(2)
        with col_pipe1:
            pipe_in = st.selectbox(
                "Vyber priemer v palcoch", options=list(PIPE_CONVERSION.keys())
            )

        with col_pipe2:
            if pipe_in:
                pipe_mm = PIPE_CONVERSION[pipe_in]
                st.metric(label=f"Priemer v milimetroch", value=f"{pipe_mm:.2f} mm")
            else:
                st.metric(label=f"Priemer v milimetroch", value="0.00 mm")

        st.markdown("---")

        st.subheader("Prehľad vybraných chladív")
        st.markdown(
            "Základné porovnanie bežne používaných chladív v klimatizácii a chladení. GWP - Global Warming Potential."
        )

        # Zobrazenie chladív
        df_chladiva = pd.DataFrame(COMMON_REFRIGERANTS).T.reset_index()
        df_chladiva.columns = [
            "Chladivo",
            "Typ",
            "GWP (Global Warming Potential)",
            "Poznámka",
        ]
        st.dataframe(df_chladiva, hide_index=True)


# --- Spustenie aplikácie ---
if __name__ == "__main__":

    # Tento kód je len pre zjednodušenie, Streamlit ho nepotrebuje, ale je dobré ho zachovať.
    # Pôvodné funkcie chladiaci_vykon() a odporucane_hodnoty() musia byť na začiatku súboru.

    # POZNÁMKA: V reálnej aplikácii by ste vložili pôvodné definície funkcii chladiaci_vykon a odporucane_hodnoty
    # priamo pred funkciu main() alebo na začiatok súboru.

    # Aby som to mohol spustiť, musím re-definovať funkcie z predchádzajúcich príspevkov:
    def chladiaci_vykon(
        objem_m3,
        plocha_m2,
        vnutorna_teplota,
        vonkajsia_teplota,
        U,
        vymena_vzduchu_za_hod,
        osvetlenie_kW,
        osoby_a_tovar_kW,
    ):
        rho = 1.2
        cp = 1005
        deltaT = vonkajsia_teplota - vnutorna_teplota
        Q_steny = U * plocha_m2 * deltaT / 1000
        Q_vzduch = objem_m3 * rho * cp * deltaT * vymena_vzduchu_za_hod / (3600 * 1000)
        Q_vnutorne = osvetlenie_kW + osoby_a_tovar_kW
        Q_celk = Q_steny + Q_vzduch + Q_vnutorne
        return Q_celk, Q_steny, Q_vzduch, Q_vnutorne

    def odporucane_hodnoty(objem_m3):
        vymena_vzduchu = max(1.0, min(5.0, round(40 / objem_m3, 1)))
        osvetlenie = round(0.05 + 0.002 * objem_m3, 2)
        osoby_tovar = round(0.1 + 0.01 * objem_m3, 2)
        return vymena_vzduchu, osvetlenie, osoby_tovar

    main()
