import os
import io
import qrcode
from datetime import datetime
from flask import Flask, render_template, request, send_file, make_response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# --------------------------------------------------
# 【設定セクション】日本語フォントの設定
# --------------------------------------------------
# お使いのOS環境に合わせて、フォントファイルのパスを正確に指定してください。
# WindowsのMSゴシックの例
FONTS_PATH = 'C:\\Windows\\Fonts\\msgothic.ttc' 
# Macの例 (例: '/System/Library/Fonts/Supplemental/MsGothic.ttc')
# FONTS_PATH = '/System/Library/Fonts/Supplemental/MsGothic.ttc'
# --------------------------------------------------
FONT_NAME = 'MS_Gothic'

# PDF設定
PAGE_SIZE = A4
MARGIN_TOP = 285 * mm
MARGIN_LEFT = 15 * mm
LINE_HEIGHT = 16
FONT_SIZE_NORMAL = 11
FONT_SIZE_LARGE = 14
FONT_SIZE_TITLE = 20

def generate_qr_code(url):
    """URLからQRコード画像を生成し、BytesIOを返す"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def create_multi_product_pdf(data_list):
    """複数の製品データから、1つのPDFファイル（各製品1ページ）を生成する"""
    
    # 1. フォントの登録 (1回のみ)
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONTS_PATH))
    except Exception as e:
        print(f"Error: 日本語フォントが見つかりません。FONTS_PATHを確認してください。: {e}")
        return None

    # 2. Canvasの作成 (メモリ上のBytesIOに)
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=PAGE_SIZE)
    width, height = PAGE_SIZE # A4 = (595.27, 841.89) points

    # 成分表示用スタイル
    styles = getSampleStyleSheet()
    ing_style = ParagraphStyle(
        name='IngredientsStyle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=FONT_SIZE_NORMAL,
        leading=LINE_HEIGHT,
        alignment=0 # 左寄せ
    )

    # 3. 各製品に対してページを生成
    for data in data_list:
        # data = {'name': ..., 'url': ..., 'ingredients': ...}
        if not data['name'] or not data['url'] or not data['ingredients']:
            continue # 空のデータはスキップ

        # 座標の基準点をリセット
        c.translate(mm, mm)
        current_y = (height / mm) - (MARGIN_TOP / mm) # 基準点を下げる (ReportLabは下から上)
        
        # --- タイトル ---
        c.setFont(FONT_NAME, FONT_SIZE_TITLE)
        c.drawCentredString(width/2 / mm, current_y, f"【スキンケア製品情報】 ({data['name']})")
        
        current_y -= 20
        
        # --- ヘッダー集約セクション (商品名、URL、QR) ---
        # 商品名
        c.setFont(FONT_NAME, FONT_SIZE_LARGE)
        c.drawString(MARGIN_LEFT / mm, current_y, "■ 商品名")
        current_y -= 7
        c.setFont(FONT_NAME, 12)
        c.drawString(MARGIN_LEFT / mm + 5, current_y, data['name'])
        
        current_y -= 15
        
        # 商品URL & QRコード (横並び)
        c.setFont(FONT_NAME, FONT_SIZE_LARGE)
        c.drawString(MARGIN_LEFT / mm, current_y, "■ 商品URL & QRコード")
        
        # QRコードの生成と描画
        qr_bytes = generate_qr_code(data['url'])
        qr_size = 35 # mm
        qr_x = (width / mm) - MARGIN_LEFT / mm - qr_size # 右上
        qr_y = current_y - (qr_size / 2) - 3 # URLの横
        c.drawImage(ImageReader(qr_bytes), qr_x * mm, qr_y * mm, width=qr_size*mm, height=qr_size*mm)

        current_y -= 7
        c.setFont(FONT_NAME, 10)
        # URL
        c.drawString(MARGIN_LEFT / mm + 5, current_y, data['url'])
        
        current_y -= 25 # QRコードの高さを考慮
        
        # --- 区切り線 ---
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.line(MARGIN_LEFT / mm, current_y, (width/mm - MARGIN_LEFT / mm), current_y)
        current_y -= 1 # 二重線風
        c.line(MARGIN_LEFT / mm, current_y, (width/mm - MARGIN_LEFT / mm), current_y)
        
        current_y -= 15
        
        # --- 全成分表示 (下部を大きく) ---
        c.setFont(FONT_NAME, FONT_SIZE_LARGE)
        c.drawString(MARGIN_LEFT / mm, current_y, "■ 全成分表示")
        
        current_y -= 8
        
        # 成分表示 (Paragraph)
        ing_p = Paragraph(data['ingredients'], ing_style)
        
        content_width = (width / mm) - (MARGIN_LEFT / mm * 2)
        p_w, p_h = ing_p.wrap(content_width * mm, (current_y) * mm)
        
        ing_p.drawOn(c, MARGIN_LEFT, (current_y - p_h/mm) * mm)

        # 次の製品のために新しいページを開始
        c.showPage()

    # 4. 保存
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # フォームデータを受け取る (配列形式)
        product_names = request.form.getlist('product_name[]')
        product_urls = request.form.getlist('product_url[]')
        ingredients_list = request.form.getlist('ingredients[]')

        # データを辞書のリストにまとめる
        data_list = []
        for name, url, ing in zip(product_names, product_urls, ingredients_list):
            data_list.append({
                'name': name.strip(),
                'url': url.strip(),
                'ingredients': ing.strip().replace('\r\n', '<br/>').replace('\n', '<br/>') # 改行をHTMLタグに変換
            })

        # PDFを生成
        pdf_buffer = create_multi_product_pdf(data_list)
        
        if pdf_buffer:
            # 生成したPDFをダウンロードさせる
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"skincare_info_{timestamp}.pdf"
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        else:
            return "Error: PDF生成に失敗しました。サーバーのログを確認してください。", 500

    return render_template('index.html')

if __name__ == '__main__':
    # サーバーを起動
    # ローカル実行なので debug=True
    app.run(debug=True, port=5000)