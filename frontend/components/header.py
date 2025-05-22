import streamlit as st


def render_tooltip_heading(title: str, explanation: str):
    st.markdown("""
    <style>
    .tooltip {
      position: relative;
      display: inline-block;
      cursor: help;
    }

    .tooltip .tooltiptext {
      visibility: hidden;
      width: 220px;
      background-color: #555;
      color: #fff;
      text-align: left;
      border-radius: 6px;
      padding: 8px;
      position: absolute;
      z-index: 1;
      bottom: 125%; 
      left: 50%;
      margin-left: 0px;
      opacity: 0;
      transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
      visibility: visible;
      opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <h5 style='text-align: left;'>
        {title}
        <span class="tooltip" style="font-size: 14px;">ⓘ
            <span class="tooltiptext">{explanation}</span>
        </span>
    </h5>
    """, unsafe_allow_html=True)
