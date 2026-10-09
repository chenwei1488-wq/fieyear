import streamlit as st
import pandas as pd
import os
import random
from backend import BackendEngine

# ==================== 页面与引擎初始化 ====================
st.set_page_config(page_title="商品管理系统 (千人千面升级版)", layout="wide")

@st.cache_resource
def get_engine():
    return BackendEngine()

engine = get_engine()

# ==================== 登录拦截 (防盗门) ====================
def login():
    st.title("🔐 Fieyear 系统登录")
    password = st.text_input("请输入管理员密码", type="password")
    if st.button("登录"):
        if password == "123456":  # 可改为 os.getenv("ADMIN_PWD")
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密码错误，请重试")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# ==================== 状态管理初始化 ====================
if "usd_rate" not in st.session_state: st.session_state.usd_rate = 7.14
if "eur_rate" not in st.session_state: st.session_state.eur_rate = 7.69
if "display_currency" not in st.session_state: st.session_state.display_currency = "EUR"

# ==================== 侧边栏导航 ====================
st.sidebar.title("chenwei \n 🟢 在线")
menu = st.sidebar.radio(
    "功能导航",
    ["👤 达人管理", "📦 商品管理", "🎨 店铺装修", "🤝 二手审核"]
)

# 获取全局达人列表供多处使用
influencers = engine.get_influencers()
inf_dict = {f"{inf[1]} (ID:{inf[0]})": inf[0] for inf in influencers} if influencers else {}
inf_name_map = {inf[0]: inf[1] for inf in influencers}

# ==================== 页面 1：达人管理 ====================
if menu == "👤 达人管理":
    st.header("👤 达人信息手动录入与管理")
    
    col_form, col_table = st.columns([1, 2])
    
    with col_form:
        with st.form("inf_form"):
            st.subheader("新增达人")
            name = st.text_input("达人名称*")
            role = st.selectbox("达人层级", ["一级 (公库)", "二级 (私库)"])
            
            # 过滤出一级达人作为公库选项
            tier1_options = {"--- 请选择要绑定的公库 ---": 0}
            for inf in influencers:
                if len(inf) > 11 and inf[11] == 'tier1':
                    tier1_options[inf[1]] = inf[0]
                    
            parent_id_name = st.selectbox("绑定公库(仅二级)", list(tier1_options.keys()))
            parent_id = tier1_options[parent_id_name]
            
            social_link = st.text_input("社交媒体链接")
            web_name = st.text_input("网页页面名称")
            web_link = st.text_input("网页页面链接")
            platform = st.selectbox("所属平台", ["Lovegobuy", "boonbuy"])
            invite_code = st.text_input("达人联盟代码")
            invite_link = st.text_input("专属邀请链接")
            invite_btn_text = st.text_input("邀请按钮文案", placeholder="默认: 🎁 S'inscrire sur Lovegobuy pour -30%")
            tutorial_link = st.text_input("专属教程链接")
            tutorial_btn_text = st.text_input("教程按钮文案", placeholder="默认: 📚 Tutoriel")
            
            submitted = st.form_submit_button("➕ 确认录入到数据库", use_container_width=True)
            if submitted:
                if not name:
                    st.error("达人名称为必填项！")
                else:
                    role_val = "tier2" if role == "二级 (私库)" else "tier1"
                    p_id = parent_id if role_val == "tier2" else 0
                    data = (name, social_link, web_name, web_link, platform, invite_code, invite_link, invite_btn_text, tutorial_link, tutorial_btn_text, role_val, p_id)
                    engine.add_influencer(data)
                    st.success("新达人已成功入库！")
                    st.rerun()

    with col_table:
        st.subheader("📋 达人信息总览列表")
        if influencers:
            # 转换为 DataFrame 方便展示
            df_inf = pd.DataFrame(influencers, columns=["ID", "名称", "社交", "网页名", "网页链接", "平台", "代码", "邀请链接", "邀请文案", "教程链接", "教程文案", "层级", "公库ID"])
            df_inf["层级"] = df_inf["层级"].apply(lambda x: "二级(私库)" if x == "tier2" else "一级(公库)")
            df_inf["所属公库"] = df_inf.apply(lambda row: inf_name_map.get(row["公库ID"], "-") if row["层级"] == "二级(私库)" else "-", axis=1)
            # 重新排序列
            df_inf = df_inf[["ID", "名称", "层级", "所属公库", "平台", "代码", "社交", "网页名", "网页链接"]]
            st.dataframe(df_inf, use_container_width=True, hide_index=True)
            
            # 删除达人操作
            del_id = st.number_input("输入要删除的达人 ID", min_value=0, step=1)
            if st.button("🗑️ 确认彻底删除该达人及其所有商品"):
                if del_id > 0:
                    engine.delete_influencer(del_id)
                    st.success(f"ID {del_id} 达人已被删除！")
                    st.rerun()

# ==================== 页面 2：商品管理 ====================
elif menu == "📦 商品管理":
    st.header("📦 商品管理")
    
    # --- 顶部工具栏 ---
    top_c1, top_c2, top_c3, top_c4, top_c5 = st.columns([3, 1, 1, 1.5, 1])
    with top_c1:
        selected_infs = st.multiselect("🎯 操作达人分配", list(inf_dict.keys()))
        selected_inf_ids = [inf_dict[k] for k in selected_infs]
    with top_c2:
        usd_rate = st.number_input("💵 美金汇率", value=st.session_state.usd_rate, step=0.01)
        st.session_state.usd_rate = usd_rate
    with top_c3:
        eur_rate = st.number_input("💶 欧元汇率", value=st.session_state.eur_rate, step=0.01)
        st.session_state.eur_rate = eur_rate
    with top_c4:
        st.write("") # 占位
        if st.button("🔄 按此汇率重算选中达人", use_container_width=True):
            if selected_inf_ids:
                engine.recalculate_foreign_currencies(usd_rate, eur_rate, selected_inf_ids)
                st.success("重算完成！")
            else:
                st.warning("请先勾选目标达人！")
    with top_c5:
        st.write("") 
        if st.button("🚀 发布网页打包", type="primary"):
            if selected_inf_ids:
                # 增加 GitHub 全自动推送逻辑
                st.info("本地文件生成完毕，正在将最新网页推送到 GitHub (这可能需要十几秒，请勿刷新)...")
                with st.spinner("云端上传中..."):
                    # 1. 触发 backend.py 里的本地打包生成逻辑
                    engine.export_web_page([], display_currency=st.session_state.display_currency, export_dir="Web_Exports")
                    
                    # 2. 触发 GitHub 自动推送逻辑
                    success, msg = engine.push_exports_to_github("Web_Exports")
                    if success:
                        st.success(msg)
                        st.balloons() # 放个庆祝气球
                    else:
                        st.error(msg)
            else:
                st.warning("请选择要打包的达人！")

    st.divider()
    
    # --- 左右布局结构 ---
    left_col, right_col = st.columns([1, 2.5])
    
    with left_col:
        tabs = st.tabs(["单品录入", "批量导入"])
        
        with tabs[0]:
            with st.form("single_product_form"):
                st.subheader("单品属性录入")
                name = st.text_input("商品名称*")
                link_type = st.radio("链接类型", ["使用平台拼接链接", "使用原链接"], horizontal=True)
                raw_link = st.text_input("微店链接*")
                source_link = st.text_input("拿货链接(内部用)")
                tk_ids = st.text_input("TikTok视频 ID (支持多ID以逗号隔开)", placeholder="例: 7123456789, 7987654321")
                
                col_img1, col_img2 = st.columns([3, 1])
                with col_img1:
                    img_path = st.text_input("商品主图 (本地路径或URL)")
                with col_img2:
                    st.write("")
                    auto_bg = st.checkbox("✨ 自动抠图")
                    
                qc_paths = st.text_input("质检图(QC) (多链接以逗号分隔)")
                
                rmb = st.text_input("基准价格 (元 RMB)*")
                
                submitted = st.form_submit_button("➕ 添加商品", use_container_width=True)
                if submitted:
                    if not name or not raw_link or not rmb:
                        st.error("名称、微店链接和价格为必填项！")
                    elif not selected_inf_ids:
                        st.error("请在顶部【操作达人分配】处选择至少一位达人！")
                    else:
                        # 汇率计算
                        r_val = float(engine.clean_price_to_string(rmb))
                        u_val = f"{(r_val / usd_rate):.2f}"
                        e_val = f"{(r_val / eur_rate):.2f}"
                        
                        for inf_id in selected_inf_ids:
                            # 查达人配置以拼接链接
                            invite_code, platform = "", "Lovegobuy"
                            for inf in influencers:
                                if inf[0] == inf_id:
                                    invite_code, platform = inf[6] or "", inf[5] or "Lovegobuy"
                                    break
                            
                            t_link = raw_link if link_type == "使用原链接" else engine.convert_link(raw_link, platform, invite_code)
                            
                            # 注意数据元组与后端一致 (含 tk_ids)
                            data = (inf_id, "", name, raw_link, t_link, r_val, u_val, e_val, img_path, qc_paths, source_link, "", tk_ids)
                            engine.add_single_product_get_id(data)
                        st.success("商品添加成功！")
                        st.rerun()
                        
        with tabs[1]:
            st.subheader("极简批量导入")
            excel_path = st.text_input("Excel 绝对路径 (A:名称 B:图片 C:类目 D:公库链接 E:价格 F:QC G:拿货链接)")
            chk_auto_bg = st.checkbox("导入时自动为所有商品图片抠去背景 (耗时较长)")
            if st.button("⚡ 开始批量导入", use_container_width=True):
                if not selected_inf_ids:
                    st.error("请选择归属达人")
                elif not os.path.exists(excel_path):
                    st.error("Excel 文件路径不存在")
                else:
                    for inf_id in selected_inf_ids:
                        count = engine.import_products_from_excel(excel_path, inf_id, chk_auto_bg)
                    st.success("批量导入完成！")
                    st.rerun()

    with right_col:
        st.subheader("公库商品列表 (客观属性)")
        
        # 提取选中达人的数据
        products = engine.get_products_by_influencers(selected_inf_ids) if selected_inf_ids else []
        
        if products:
            # 转化为 DataFrame 以支持 Streamlit Data Editor
            cols = ["ID", "归属达人ID", "类目", "名称", "转化链接", "RMB", "USD", "EUR", "图片", "QC", "内部源", "子类目", "创建时间", "TK_IDs"]
            df = pd.DataFrame(products, columns=cols)
            
            # 插入一列用于复选
            df.insert(0, "选择", False)
            # 价格展示处理
            display_curr = st.session_state.display_currency
            if display_curr == "EUR": df["展示价格"] = df["EUR"].apply(lambda x: f"€{x}")
            elif display_curr == "USD": df["展示价格"] = df["USD"].apply(lambda x: f"${x}")
            else: df["展示价格"] = df["RMB"].apply(lambda x: f"¥{x}")
            
            df["归属达人"] = df["归属达人ID"].apply(lambda x: inf_name_map.get(x, "未知"))
            
            display_df = df[["选择", "ID", "归属达人", "名称", "展示价格", "转化链接", "TK_IDs", "图片", "QC", "内部源", "类目", "子类目"]]
            
            # 使用可编辑表格
            edited_df = st.data_editor(
                display_df,
                hide_index=True,
                use_container_width=True,
                column_config={"选择": st.column_config.CheckboxColumn("勾选", default=False)}
            )
            
            # 批量操作栏
            selected_rows = edited_df[edited_df["选择"] == True]
            selected_pids = selected_rows["ID"].tolist()
            
            st.markdown("---")
            b_col1, b_col2, b_col3 = st.columns(3)
            
            with b_col1:
                # 提取QC功能
                src_qc_id = st.number_input("输入源商品ID以提取QC", min_value=0)
                if st.button("🧲 提取指定QC并覆盖选中商品"):
                    if not selected_pids: st.warning("请在表格中勾选目标商品")
                    elif src_qc_id > 0:
                        source_row = engine.get_product_by_id(src_qc_id)
                        source_qc = source_row[10] if source_row and len(source_row) > 10 else ""
                        if source_qc:
                            for pid in selected_pids:
                                old = engine.get_product_by_id(pid)
                                new_data = (old[1], old[2], old[3], old[4], old[5], old[6], old[7], old[8], old[9], source_qc, old[12] if len(old)>12 else "", old[13] if len(old)>13 else "", old[17] if len(old)>17 else "")
                                engine.update_product(pid, new_data)
                            st.success("QC 提取覆盖完成！")
                            st.rerun()
            
            with b_col2:
                # 批量删除
                if st.button("🗑️ 物理删除选中的商品", type="primary"):
                    if selected_pids:
                        engine.delete_products(selected_pids)
                        st.success(f"删除了 {len(selected_pids)} 个商品！")
                        st.rerun()
                    else:
                        st.warning("未勾选任何商品！")
            
            with b_col3:
                # 呈现币种切换
                new_curr = st.selectbox("切换界面呈现货币", ["EUR", "USD", "RMB"], index=["EUR", "USD", "RMB"].index(st.session_state.display_currency))
                if new_curr != st.session_state.display_currency:
                    st.session_state.display_currency = new_curr
                    st.rerun()
        else:
            st.info("请在顶部选择达人以加载公库商品列表。")

# ==================== 页面 3：店铺装修 ====================
elif menu == "🎨 店铺装修":
    st.header("🎨 店铺装修 (前台货架管理)")
    
    dec_c1, dec_c2 = st.columns([1, 3])
    
    with dec_c1:
        st.subheader("👤 达人专属类目管理")
        target_inf = st.selectbox("选择要装修的达人", list(inf_dict.keys()), key="deco_inf")
        inf_id = inf_dict.get(target_inf)
        
        if inf_id:
            tree = engine.get_categories_tree(inf_id)
            # 将树状结构展平供 Selectbox 选择
            cat_options = []
            for main in tree:
                cat_options.append(f"📂 {main['name']}")
                for sub in main["subCategories"]:
                    cat_options.append(f" ↳ 🏷️ {main['name']} > {sub['name']}")
                    
            selected_cat_str = st.selectbox("选择要排布的类目", cat_options) if cat_options else None
            
            # 解析选中的类目
            main_cat, sub_cat = None, None
            if selected_cat_str:
                if selected_cat_str.startswith("📂"):
                    main_cat = selected_cat_str.replace("📂 ", "")
                else:
                    parts = selected_cat_str.replace(" ↳ 🏷️ ", "").split(" > ")
                    main_cat, sub_cat = parts[0], parts[1]

            st.divider()
            new_main = st.text_input("新增主类目名称")
            if st.button("➕ 添加主类目"):
                if new_main: engine.add_category(inf_id, new_main); st.rerun()

    with dec_c2:
        if not inf_id or not selected_cat_str:
            st.info("请在左侧选择达人及具体类目后进行装修。")
        else:
            st.subheader(f"📱 货架内容排布: {selected_cat_str}")
            st.write("在 Streamlit 中，我们通过直接修改序号来完成排序 (数字越小越靠前)：")
            
            # 获取该类目下的商品
            all_prods = engine.get_products_by_influencers([inf_id])
            if sub_cat:
                canvas_data = [p for p in all_prods if p[2] == main_cat and p[11] == sub_cat]
            else:
                canvas_data = [p for p in all_prods if p[2] == main_cat and (not p[11])]
            
            if canvas_data:
                df_canvas = pd.DataFrame(canvas_data, columns=["ID", "Inf", "类目", "名称", "链接", "RMB", "USD", "EUR", "IMG", "QC", "SRC", "子类目", "Time", "TK"])
                # 增加一列用于模拟排序 (默认0)
                df_canvas.insert(0, "排序号", range(len(df_canvas)))
                
                edited_canvas = st.data_editor(
                    df_canvas[["排序号", "ID", "名称", "EUR"]], 
                    use_container_width=True, 
                    hide_index=True
                )
                
                if st.button("💾 保存货架顺序"):
                    # 根据排序号升序排列提取 ID
                    sorted_df = edited_canvas.sort_values(by="排序号")
                    ordered_ids = sorted_df["ID"].tolist()
                    engine.update_sort_orders(ordered_ids)
                    st.success("货架顺序已更新生效！")
            else:
                st.warning("当前类目下没有商品。请前往【商品管理】进行添加或转移。")

# ==================== 页面 4：二手审核 ====================
elif menu == "🤝 二手审核":
    st.header("🤝 C2C 二手交易审核中心")
    
    posts = engine.get_resell_posts()
    if posts:
        df_resell = pd.DataFrame(posts, columns=["ID", "状态", "卖家DC", "名称", "图片", "价格", "购买链接", "操作", "创建时间"])
        status_map = {'pending': '🟡 待审核', 'approved': '🟢 已通过', 'rejected': '🔴 已驳回'}
        df_resell["状态"] = df_resell["状态"].map(status_map)
        
        st.dataframe(df_resell[["ID", "状态", "名称", "价格", "卖家DC", "购买链接", "创建时间"]], use_container_width=True, hide_index=True)
        
        st.subheader("🛠️ 审核操作")
        act_c1, act_c2 = st.columns(2)
        with act_c1:
            target_post_id = st.number_input("输入要操作的帖子 ID", min_value=0, step=1)
        with act_c2:
            st.write("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ 通过审核 (自动存图)", type="primary", use_container_width=True):
                    if target_post_id > 0:
                        # 执行之前代码里的逻辑：通过并提取图片
                        conn = __import__('sqlite3').connect(engine.DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("SELECT image_url FROM resell_posts WHERE id=?", (target_post_id,))
                        row = cursor.fetchone()
                        original_img_url = row[0] if row else ""
                        final_img_url = original_img_url
                        
                        if original_img_url and original_img_url.startswith("http") and ".r2.dev" not in original_img_url:
                            cdn_url = engine.process_image_pipeline(original_img_url, "resell", f"post_{target_post_id}", is_qc=False)
                            if cdn_url: final_img_url = cdn_url
                                
                        cursor.execute("UPDATE resell_posts SET status=?, image_url=? WHERE id=?", ('approved', final_img_url, target_post_id))
                        conn.commit(); conn.close()
                        st.success(f"ID {target_post_id} 审核通过！")
                        st.rerun()
            with col_btn2:
                if st.button("❌ 驳回/撤销下架", use_container_width=True):
                    if target_post_id > 0:
                        engine.update_resell_status(target_post_id, 'rejected')
                        st.success(f"ID {target_post_id} 已驳回！")
                        st.rerun()
    else:
        st.info("目前没有任何二手交易发帖记录。")