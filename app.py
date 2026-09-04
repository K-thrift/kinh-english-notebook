import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Smart English Notebook",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Giao diện thẻ màu phong cách sổ tay
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .notebook-sheet {
        background: #ffffff;
        border-radius: 18px;
        padding: 28px 32px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        border: 1px solid #f1f3f5;
        margin-bottom: 25px;
    }
    
    .article-title {
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 6px;
    }
    
    .article-url {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 24px;
    }
    
    .vocab-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
    }
    
    .vocab-word {
        font-size: 18px;
        font-weight: 700;
        color: #166534;
    }
    
    .vocab-ipa {
        font-size: 14px;
        color: #15803d;
        background: #ffffffaa;
        padding: 2px 8px;
        border-radius: 6px;
        font-family: monospace;
        margin-left: 8px;
    }
    
    .vocab-pos {
        font-size: 12px;
        color: #475569;
        font-style: italic;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 6px;
    }
    
    .vocab-def {
        font-size: 14px;
        color: #1e293b;
        margin-top: 8px;
        font-weight: 500;
    }
    
    .vocab-example {
        font-size: 13px;
        color: #475569;
        background: #ffffff88;
        padding: 8px 12px;
        border-left: 3px solid #22c55e;
        border-radius: 4px;
        margin-top: 8px;
        font-style: italic;
    }
    
    .passage-card {
        background: linear-gradient(135deg, #fefce8 0%, #fef08a 100%);
        border: 1px solid #fef08a;
        border-radius: 14px;
        padding: 20px;
        color: #854d0e;
        line-height: 1.7;
        font-size: 15px;
        margin-top: 15px;
    }

    .edit-box {
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Kết nối Google Sheets độc lập theo từng Secret của App
conn = st.connection("gsheets", type=GSheetsConnection)
target_sheet = st.secrets["connections"]["gsheets"]["spreadsheet"]


def load_data():
  required_cols = ["page_id", "title", "source_url", "vocab_list", "passage"]
  try:
    data = conn.read(spreadsheet=target_sheet, ttl=0)
    if data is None or data.empty or not set(required_cols).issubset(data.columns):
      data = pd.DataFrame(columns=required_cols)
    else:
      data["page_id"] = pd.to_numeric(data["page_id"], errors="coerce").fillna(1)
      data = data.sort_values(by="page_id").reset_index(drop=True)
  except Exception:
    data = pd.DataFrame(columns=required_cols)
  return data


df = load_data()


# Nút phát âm trực tiếp bằng giọng đọc trình duyệt
def render_audio_button(text, button_id):
  escaped = text.replace('"', '\\"').replace("\n", " ")
  html_code = f"""
    <button onclick="speakText_{button_id}()" style="
        background-color: #3b82f6; color: white; border: none; 
        border-radius: 50%; width: 28px; height: 28px; cursor: pointer; 
        font-size: 13px; line-height: 28px; text-align: center; display: inline-block;">
        🔊
    </button>
    <script>
    function speakText_{button_id}() {{
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{escaped}");
        msg.lang = 'en-US';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
    }}
    </script>
    """
  components.html(html_code, height=36, width=45)


# Quản lý số trang
max_pages = int(df["page_id"].max()) if not df.empty else 1
if "page_idx" not in st.session_state:
  st.session_state.page_idx = 1

# Thanh chuyển bài lật trang
header_col1, header_col2, header_col3 = st.columns([1, 2, 1])
with header_col1:
  if st.button("◀ Trang trước") and st.session_state.page_idx > 1:
    st.session_state.page_idx -= 1
    st.rerun()

with header_col2:
  st.markdown(
      f"<div style='text-align: center; font-size: 18px; font-weight: 700;"
      f" color: #3b82f6;'>Trang {st.session_state.page_idx} /"
      f" {max(max_pages, st.session_state.page_idx)}</div>",
      unsafe_allow_html=True,
  )

with header_col3:
  if st.button("Trang sau ▶"):
    st.session_state.page_idx += 1
    st.rerun()

st.write("")

# Lấy dữ liệu bài hiện tại
current_row = df[df["page_id"] == st.session_state.page_idx]
row = current_row.iloc[0] if not current_row.empty else None

tab_learn, tab_input = st.tabs(["📖 Học bài", "✏️ Soạn / Sửa bài trang này"])

# ================= TAB 1: GIAO DIỆN HỌC BÀI =================
with tab_learn:
  if row is not None and pd.notna(row.get("title")):
    st.markdown(
        f"""
        <div class="notebook-sheet">
            <div class="article-title">{row.get('title', '')}</div>
            <div class="article-url">🔗 Nguồn bài: <a href="{row.get('source_url', '#')}" target="_blank">{row.get('source_url', 'Không có link')}</a></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([3, 2])

    with col_left:
      st.markdown(
          "<h4 style='color: #0f172a; margin-bottom: 15px;'>🌱 Danh mục Từ vựng"
          " đã nhặt</h4>",
          unsafe_allow_html=True,
      )

      vocab_items = []
      try:
        raw_vocab = row.get("vocab_list", "[]")
        vocab_items = (
            json.loads(raw_vocab)
            if isinstance(raw_vocab, str) and raw_vocab.startswith("[")
            else []
        )
      except Exception:
        vocab_items = []

      if vocab_items:
        for idx, item in enumerate(vocab_items):
          word = item.get("word", "")
          ipa = item.get("ipa", "")
          pos = item.get("pos", "")
          definition = item.get("def", "")
          example = item.get("example", "")

          c1, c2 = st.columns([11, 1])
          with c1:
            st.markdown(
                f"""
                        <div class="vocab-card">
                            <span class="vocab-word">{word}</span>
                            <span class="vocab-ipa">{ipa}</span>
                            <span class="vocab-pos">{pos}</span>
                            <div class="vocab-def">👉 {definition}</div>
                            {f'<div class="vocab-example">“ {example} ”</div>' if example else ''}
                        </div>
                        """,
                unsafe_allow_html=True,
            )
          with c2:
            render_audio_button(word, f"w_{idx}")
      else:
        st.info("Chưa có từ vựng nào được thêm cho bài báo này.")

    with col_right:
      st.markdown(
          "<h4 style='color: #0f172a; margin-bottom: 15px;'>📑 Đoạn văn mẫu"
          " trích bài báo</h4>",
          unsafe_allow_html=True,
      )
      passage = row.get("passage", "")
      if passage:
        st.markdown(
            f'<div class="passage-card">{passage}</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        st.caption("Nghe đọc cả đoạn mẫu:")
        render_audio_button(passage, "passage_btn")
      else:
        st.info("Chưa có đoạn văn trích dẫn mẫu.")
  else:
    st.info(
        f"Trang {st.session_state.page_idx} chưa có bài học. Hãy chuyển sang"
        " tab 'Soạn / Sửa bài trang này' để thêm bài mới!"
    )

# ================= TAB 2: SOẠN BÀI =================
with tab_input:
  default_title = row["title"] if row is not None else ""
  default_url = row["source_url"] if row is not None else ""
  default_passage = row["passage"] if row is not None else ""

  existing_vocab = []
  if row is not None:
    try:
      raw = row.get("vocab_list", "[]")
      existing_vocab = (
          json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else []
      )
    except Exception:
      existing_vocab = []

  state_key = f"vocab_cards_{st.session_state.page_idx}"
  if state_key not in st.session_state:
    st.session_state[state_key] = (
        existing_vocab
        if existing_vocab
        else [{"word": "", "ipa": "", "pos": "noun", "def": "", "example": ""}]
    )

  st.markdown("### 📰 1. Thông tin bài báo")
  in_title = st.text_input("Tiêu đề bài báo", value=default_title)
  in_url = st.text_input("Đường link bài báo", value=default_url)

  st.markdown("---")
  st.markdown("### 🗂️ 2. Thẻ từ vựng (Nhập từng ô phân loại)")

  indices_to_delete = []
  for i, card in enumerate(st.session_state[state_key]):
    st.markdown(
        f"<div class='edit-box'><b>Thẻ từ #{i+1}</b></div>",
        unsafe_allow_html=True,
    )
    col_w, col_ipa, col_pos, col_del = st.columns([3, 2, 2, 1])

    with col_w:
      card["word"] = st.text_input(
          f"Từ vựng #{i+1}", value=card.get("word", ""), key=f"word_{i}"
      )
    with col_ipa:
      card["ipa"] = st.text_input(
          f"Phiên âm IPA #{i+1}",
          value=card.get("ipa", ""),
          placeholder="/.../",
          key=f"ipa_{i}",
      )
    with col_pos:
      card["pos"] = st.selectbox(
          f"Loại từ #{i+1}",
          options=[
              "noun",
              "verb",
              "adj",
              "adv",
              "idiom",
              "phrasal verb",
              "other",
          ],
          index=[
              "noun",
              "verb",
              "adj",
              "adv",
              "idiom",
              "phrasal verb",
              "other",
          ].index(card.get("pos", "noun"))
          if card.get("pos")
          in [
              "noun",
              "verb",
              "adj",
              "adv",
              "idiom",
              "phrasal verb",
              "other",
          ]
          else 0,
          key=f"pos_{i}",
      )
    with col_del:
      st.write("")
      st.write("")
      if st.button("🗑️", key=f"del_{i}", help="Xóa từ này"):
        indices_to_delete.append(i)

    col_def, col_ex = st.columns([3, 4])
    with col_def:
      card["def"] = st.text_input(
          f"Định nghĩa / Nghĩa #{i+1}",
          value=card.get("def", ""),
          key=f"def_{i}",
      )
    with col_ex:
      card["example"] = st.text_input(
          f"Câu ví dụ #{i+1}",
          value=card.get("example", ""),
          placeholder="Ví dụ trích từ bài...",
          key=f"ex_{i}",
      )

  if indices_to_delete:
    for idx in sorted(indices_to_delete, reverse=True):
      st.session_state[state_key].pop(idx)
    st.rerun()

  if st.button("➕ Thêm ô từ vựng mới"):
    st.session_state[state_key].append(
        {"word": "", "ipa": "", "pos": "noun", "def": "", "example": ""}
    )
    st.rerun()

  st.markdown("---")
  st.markdown("### 📑 3. Đoạn văn mẫu nguyên bản")
  in_passage = st.text_area(
      "Đoạn văn trích dẫn từ bài báo",
      value=default_passage,
      height=130,
      placeholder="Dán đoạn văn tâm đắc chứa ngữ cảnh bài báo vào đây...",
  )

  if st.button("💾 Lưu toàn bộ trang này", type="primary"):
    filtered_vocab = [
        item
        for item in st.session_state[state_key]
        if item.get("word", "").strip()
    ]

    new_row = {
        "page_id": int(st.session_state.page_idx),
        "title": str(in_title),
        "source_url": str(in_url),
        "vocab_list": json.dumps(filtered_vocab, ensure_ascii=False),
        "passage": str(in_passage),
    }

    if row is not None:
      idx_to_update = df[df["page_id"] == st.session_state.page_idx].index[0]
      for c, v in new_row.items():
        df.at[idx_to_update, c] = v
    else:
      df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    conn.update(spreadsheet=target_sheet, data=df)
    st.success(f"Đã lưu trang {st.session_state.page_idx} vào sổ thành công!")
    st.rerun()
