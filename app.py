import os
import io
import qrcode
from datetime import datetime
from flask import Flask, render_template, request, send_file
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
FONTS_PATH = 'C:\\Windows\\Fonts\\msgothic.ttc' 
FONT_NAME = 'MS_Gothic'

PAGE_SIZE = A4

def generate_qr_code(url):
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
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONTS_PATH))
    except Exception as e:
        print(f"Error: 日本語フォントが見つかりません。: {e}")
        return None

    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=PAGE_SIZE)
    width, height = PAGE_SIZE # A4 = (595.27, 841.89) ポイント

    styles = getSampleStyleSheet()
    ing_style = ParagraphStyle(
        name='IngredientsStyle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=16,
        alignment=0 
    )

    for data in data_list:
        if not data['name'] or not data['url'] or not data['ingredients']:
            continue 

        # ReportLabの座標は左下(0,0)なので、用紙の一番上(height)から引き算して位置を決めます。
        margin_left = 15 * mm
        current_y = height - (20 * mm) # 上から20mmの位置からスタート
        
        # --- タイトル ---
        c.setFont(FONT_NAME, 20)
        c.drawCentredString(width / 2.0, current_y, f"【スキンケア製品情報】 ({data['name']})")
        
        current_y -= 15 * mm
        
        # --- ヘッダー集約セクション (商品名、URL、QR) ---
        c.setFont(FONT_NAME, 14)
        c.drawString(margin_left, current_y, "■ 商品名")
        current_y -= 7 * mm
        
        c.setFont(FONT_NAME, 12)
        c.drawString(margin_left + (5 * mm), current_y, data['name'])
        
        current_y -= 15 * mm
        
        # 商品URL & QRコード
        c.setFont(FONT_NAME, 14)
        c.drawString(margin_left, current_y, "■ 商品URL & QRコード")
        
        # QRコードの描画位置調整
        qr_size = 35 * mm
        qr_x = width - margin_left - qr_size 
        qr_y = current_y - (25 * mm) # URLの横に綺麗に収まるようにY座標を調整
        
        qr_bytes = generate_qr_code(data['url'])
        c.drawImage(ImageReader(qr_bytes), qr_x, qr_y, width=qr_size, height=qr_size)

        current_y -= 7 * mm
        c.setFont(FONT_NAME, 10)
        c.drawString(margin_left + (5 * mm), current_y, data['url'])
        
        current_y -= 25 * mm 
        
        # --- 区切り線 ---
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.line(margin_left, current_y, width - margin_left, current_y)
        current_y -= 1 * mm 
        c.line(margin_left, current_y, width - margin_left, current_y)
        
        current_y -= 15 * mm
        
        # --- 全成分表示 ---
        c.setFont(FONT_NAME, 14)
        c.drawString(margin_left, current_y, "■ 全成分表示")
        
        current_y -= 8 * mm
        
        # 成分表示 (Paragraph) は長文になるため、領域を計算して描画します
        ing_p = Paragraph(data['ingredients'], ing_style)
        content_width = width - (margin_left * 2)
        p_w, p_h = ing_p.wrap(content_width, current_y - (15 * mm))
        
        ing_p.drawOn(c, margin_left, current_y - p_h)

        c.showPage()

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_names = request.form.getlist('product_name[]')
        product_urls = request.form.getlist('product_url[]')
        ingredients_list = request.form.getlist('ingredients[]')

        data_list = []
        for name, url, ing in zip(product_names, product_urls, ingredients_list):
            data_list.append({
                'name': name.strip(),
                'url': url.strip(),
                'ingredients': ing.strip().replace('\r\n', '<br/>').replace('\n', '<br/>')
            })

        pdf_buffer = create_multi_product_pdf(data_list)
        
        if pdf_buffer:
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
    app.run(debug=True, port=5000)