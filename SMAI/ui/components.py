from __future__ import annotations

from typing import Dict, List

import streamlit as st


def kpi_card(label: str, value: str, delta: str | None = None, delta_color: str = "neutral") -> None:
    color = {"good": "#2ecc71", "bad": "#ff5c5c", "neutral": "#9fb0c3"}.get(delta_color, "#9fb0c3")
    delta_html = f"<div style='margin-top:6px;color:{color};font-size:13px'>{delta}</div>" if delta else ""
    st.markdown(
        f"""
      <div style="
        background: rgba(17,26,36,0.85);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 14px 16px;
        min-height: 86px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      ">
        <div style="color:#9fb0c3;font-size:12px;letter-spacing:0.06em;text-transform:uppercase">{label}</div>
        <div style="color:#e9eef6;font-size:32px;font-weight:700;line-height:1.1">{value}</div>
        {delta_html}
      </div>
    """,
        unsafe_allow_html=True,
    )


def render_news_bullets(items: List[Dict], title_key: str = "title", link_key: str = "link") -> None:
    if not items:
        st.info("Sem notícias disponíveis no momento.")
        return
    for it in items:
        title = it.get(title_key, "")
        link = it.get(link_key, "")
        published = it.get("published", "")
        publisher = it.get("publisher", "")
        subtitle = ""
        if publisher or published:
            subtitle = f"<span style='color:#9fb0c3'>({publisher} {published})</span>"
        if link:
            st.markdown(f"- [{title}]({link}) {subtitle}")
        else:
            st.markdown(f"- {title} {subtitle}")
