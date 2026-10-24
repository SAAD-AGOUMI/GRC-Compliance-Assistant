"""
Page Streamlit « Analyse d'écarts ».

- lance l'analyse d'écarts (toutes les mesures ou une sélection) ;
- affiche les taux de conformité et la matrice (statut en couleur et en texte) ;
- affiche le détail d'une mesure sélectionnée (critères, preuves, écart, recommandation) ;
- permet de télécharger la matrice de conformité au format Excel.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from utils.auth_local import require_login

st.set_page_config(page_title="Analyse d'écarts", page_icon="🛡️", layout="wide")
require_login()

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from Compliance.evaluate_control import ICONES, load_referentiel  # noqa: E402
from Compliance.run_audit import (  # noqa: E402
    COULEURS, compute_stats, load_latest, run_and_export,
)

st.title("🛡️ Analyse d'écarts – ISO/IEC 27002:2022")
st.caption("Évaluation de la documentation de sécurité au regard des 93 mesures "
           "de l'ISO 27002. Le verdict est une aide : il doit être validé par un auditeur.")

# ---------------------------------------------------------
# Chargement du dernier audit
# ---------------------------------------------------------
if "audit" not in st.session_state:
    st.session_state["audit"] = load_latest()

referentiel = load_referentiel()
themes = list(dict.fromkeys(m["theme"] for m in referentiel["mesures"]))

# ---------------------------------------------------------
# Lancement (administrateur uniquement : chaque mesure appelle l'API)
# ---------------------------------------------------------
with st.expander("▶️ Lancer une analyse", expanded=st.session_state["audit"] is None):
    if st.session_state.get("username") != "admin":
        st.info("Seul l'administrateur peut lancer une analyse.")
    else:
        mode = st.radio("Périmètre", ["Toutes les mesures", "Par thème", "Mesures choisies"],
                        horizontal=True)
        ids, sel_themes = None, None
        if mode == "Par thème":
            sel_themes = st.multiselect("Thèmes", themes, default=themes[:1])
        elif mode == "Mesures choisies":
            options = {f"{m['id']} – {m['titre']}": m["id"] for m in referentiel["mesures"]}
            ids = [options[o] for o in st.multiselect("Mesures", list(options))]

        if st.button("Lancer l'analyse d'écarts", type="primary"):
            bar = st.progress(0.0, text="Préparation…")

            def _progress(i, total, mesure):
                if mesure:
                    bar.progress(i / total, text=f"{i + 1}/{total} – {mesure['id']} {mesure['titre']}")
                else:
                    bar.progress(1.0, text="Terminé")

            results, stats, json_path, xlsx_path = run_and_export(ids, sel_themes, _progress)
            st.session_state["audit"] = {"resultats": results, "stats": stats,
                                         "xlsx": str(xlsx_path)}
            st.success(f"Analyse terminée : {len(results)} mesures évaluées.")

audit = st.session_state["audit"]
if not audit:
    st.info("Aucune analyse disponible. Lancez une analyse pour commencer.")
    st.stop()

results = audit["resultats"]
stats = audit.get("stats") or compute_stats(results)

# ---------------------------------------------------------
# Indicateurs
# ---------------------------------------------------------
g = stats["global"]
cols = st.columns(6)
cols[0].metric("Taux de conformité", f"{g['Taux de conformité (%)']} %")
cols[1].metric("Taux pondéré", f"{g['Taux pondéré (%)']} %")
for col, statut in zip(cols[2:], ["conforme", "partiellement conforme", "non conforme", "non traitée"]):
    col.metric(f"{ICONES[statut]} {statut.capitalize()}", g[statut.capitalize()])

with st.expander("Détail par thème et par article NIS2"):
    st.dataframe(pd.DataFrame(stats["par_theme"]), hide_index=True, use_container_width=True)
    if stats["par_nis2"]:
        st.dataframe(pd.DataFrame(stats["par_nis2"]), hide_index=True, use_container_width=True)

# ---------------------------------------------------------
# Matrice
# ---------------------------------------------------------
st.subheader("Matrice de conformité")
filtre = st.multiselect("Filtrer par statut", list(COULEURS), default=list(COULEURS))
table = pd.DataFrame([
    {"ID": r["id"], "Thème": r["theme"], "Mesure": r["titre"],
     "Statut": r["statut"],
     "Critères": f"{len(r['criteres_couverts'])}/{len(r['criteres'])}",
     "Sources": " ; ".join(r.get("sources") or []) or "—",
     "NIS2": ", ".join(r.get("nis2", []))}
    for r in results if r["statut"] in filtre
])


def _style_statut(value):
    fond, texte = COULEURS.get(value, ("FFFFFF", "000000"))
    return f"background-color: #{fond}; color: #{texte}; font-weight: bold"


selection = None
if table.empty:
    st.warning("Aucune mesure ne correspond au filtre.")
else:
    event = st.dataframe(
        table.style.map(_style_statut, subset=["Statut"]),
        hide_index=True, use_container_width=True,
        on_select="rerun", selection_mode="single-row",
    )
    if event.selection.rows:
        selection = table.iloc[event.selection.rows[0]]["ID"]

# ---------------------------------------------------------
# Détail d'une mesure
# ---------------------------------------------------------
st.subheader("Détail d'une mesure")
if selection is None:
    st.caption("Cliquez sur une ligne de la matrice pour afficher son détail.")
else:
    r = next(x for x in results if x["id"] == selection)
    st.markdown(f"### {r['id']} – {r['titre']}")
    st.markdown(f"{ICONES.get(r['statut'], '')} **Statut : {r['statut']}**"
                + (f"  ·  NIS2 : {', '.join(r['nis2'])}" if r.get("nis2") else ""))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Critères couverts**")
        for c in r["criteres_couverts"] or ["—"]:
            st.markdown(f"- ✅ {c}" if c != "—" else "- —")
    with c2:
        st.markdown("**Critères manquants**")
        for c in r["criteres_manquants"] or ["—"]:
            st.markdown(f"- ❌ {c}" if c != "—" else "- —")

    noms = {"critere": "Critère", "doc": "Document", "page": "Page", "extrait": "Extrait"}
    if r["preuves"]:
        st.markdown("**Preuves (critères couverts)**")
        st.dataframe(pd.DataFrame(r["preuves"]).rename(columns=noms),
                     hide_index=True, use_container_width=True)
    if r.get("constats"):
        st.markdown("**Constats (critères manquants)**")
        st.dataframe(pd.DataFrame(r["constats"]).rename(columns=noms),
                     hide_index=True, use_container_width=True)
    if r.get("sources"):
        st.success("📚 Sources : " + " ; ".join(r["sources"]))
    else:
        st.info("📚 Sources : aucun passage de la documentation ne justifie ce verdict.")
    if r.get("contradictions"):
        st.warning(f"Contradictions : {r['contradictions']}")
    if r.get("ecart"):
        st.markdown(f"**Écart :** {r['ecart']}")
    if r.get("recommandation"):
        st.markdown(f"**Recommandation :** {r['recommandation']}")
    if r.get("avertissements"):
        with st.expander("Contrôles automatiques"):
            for a in r["avertissements"]:
                st.markdown(f"- {a}")
    if r.get("sources_consultees"):
        st.caption("Sources consultées : " + " ; ".join(r["sources_consultees"]))

# ---------------------------------------------------------
# Téléchargement
# ---------------------------------------------------------
xlsx = audit.get("xlsx")
if not xlsx:
    files = sorted((ROOT_DIR / "Compliance" / "resultats").glob("audit_*.xlsx"))
    xlsx = str(files[-1]) if files else None
if xlsx and Path(xlsx).exists():
    st.download_button(
        "📥 Télécharger la matrice de conformité (Excel)",
        data=Path(xlsx).read_bytes(),
        file_name=Path(xlsx).name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
