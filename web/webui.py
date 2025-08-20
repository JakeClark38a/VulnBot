import sys

import streamlit as st
import streamlit_antd_components as sac

from server.utils.utils import api_address
from config.config import Configs
from web.knowledge_base.knowledge_base import knowledge_base_page
from web.utils.utils import ApiRequest

api = ApiRequest(base_url=api_address())

if __name__ == "__main__":

    st.markdown(
        """
        <style>
        [data-testid="stSidebarUserContent"] {
            padding-top: 20px;
        }
        .block-container {
            padding-top: 25px;
        }
        [data-testid="stBottomBlockContainer"] {
            padding-bottom: 20px;
        }
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        menu_items = []
        if Configs.basic_config.enable_knowledge_base:
            menu_items.append(sac.MenuItem("Knowledge Base Management", icon="hdd-stack"))

        if not menu_items:
            st.info("Knowledge base features are disabled.")
            selected_page = None
        else:
            selected_page = sac.menu(
                menu_items,
                key="selected_page",
                open_index=0,
            )
            sac.divider()

    if (
        selected_page == "Knowledge Base Management"
        and Configs.basic_config.enable_knowledge_base
    ):
        knowledge_base_page(api=api)
