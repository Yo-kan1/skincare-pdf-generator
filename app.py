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
FONTS_PATH = 'C:\\Windows\\Fonts\\msgothic.ttc' 
FONT_NAME = 'MS_Gothic'
PAGE_SIZE = A4
# --------------------------------------------------

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
    width, height = PAGE_SIZE

    styles = getSampleStyleSheet()
    ing_style = ParagraphStyle(
        name='IngredientsStyle', parent=styles['Normal'],
        fontName=FONT_NAME, fontSize=11, leading=16, alignment=0 
    )
    
    url_style = ParagraphStyle(
        name='URLStyle', parent=styles['Normal'],
        fontName=FONT_NAME, fontSize=9, leading=12, alignment=0 
    )

    for data in data_list:
        if not data['name'] or not data['url'] or not data['ingredients']:
            continue 

        margin_left = 15 * mm
        current_y = height - (20 * mm)
        
        # --- タイトル ---
        c.setFont(FONT_NAME, 20)
        c.drawCentredString(width / 2.0, current_y, f"【スキンケア製品情報】")
        
        # --- ヘッダー領域の開始位置 ---
        current_y -= 15 * mm
        box_top = current_y
        
        # 1. 右側：QRコード
        qr_size = 35 * mm
        qr_x = width - margin_left - qr_size
        qr_y = box_top - qr_size
        
        qr_bytes = generate_qr_code(data['url'])
        c.drawImage(ImageReader(qr_bytes), qr_x, qr_y, width=qr_size, height=qr_size)
        
        img_x_for_url = qr_x # デフォルトはQRコードの左端までURLを許可
        
        # 2. 中央：商品画像
        if data.get('image_data'):
            try:
                img_io = io.BytesIO(data['image_data'])
                img_box_width = 40 * mm
                img_box_height = 35 * mm # QRコードと同じ高さに設定
                img_x = qr_x - img_box_width - (5 * mm) # QRの左隣に5mm間隔で配置
                img_y = box_top - img_box_height
                
                # anchor='c' で中央揃え、縮尺を維持して枠内に収める
                c.drawImage(ImageReader(img_io), img_x, img_y, 
                            width=img_box_width, height=img_box_height, 
                            preserveAspectRatio=True, anchor='c')
                img_x_for_url = img_x # 画像がある場合は、画像の左端までURLを許可
            except Exception as e:
                print(f"画像描画エラー: {e}")
        
        # 3. 左側：商品名とURLテキスト
        c.setFont(FONT_NAME, 14)
        c.drawString(margin_left, box_top - (5 * mm), "■ 商品名")
        c.setFont(FONT_NAME, 12)
        c.drawString(margin_left + (5 * mm), box_top - (12 * mm), data['name'])
        
        c.setFont(FONT_NAME, 14)
        c.drawString(margin_left, box_top - (22 * mm), "■ 商品URL")
        
        # 長いURLが画像に被らないよう、自動改行させて描画
        available_url_width = img_x_for_url - margin_left - (5 * mm)
        url_p = Paragraph(data['url'], url_style)
        u_w, u_h = url_p.wrap(available_url_width, 30 * mm)
        url_p.drawOn(c, margin_left + (5 * mm), box_top - (24 * mm) - u_h)
        
        # --- 区切り線 ---
        current_y = box_top - qr_size - (10 * mm) # 画像・QRの下に10mmの余白
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
        for i in range(len(product_names)):
            name = product_names[i].strip()
            url = product_urls[i].strip()
            ing = ingredients_list[i].strip().replace('\r\n', '<br/>').replace('\n', '<br/>')
            
            # 画像を取得
            image_file = request.files.get(f'product_image_{i}')
            img_data = None
            if image_file and image_file.filename != '':
                img_data = image_file.read()

            data_list.append({
                'name': name,
                'url': url,
                'ingredients': ing,
                'image_data': img_data
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
            return "Error: PDF生成に失敗しました。", 500

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)