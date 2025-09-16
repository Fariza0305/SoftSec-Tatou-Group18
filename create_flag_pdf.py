# create_flag_pdf.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_flag_pdf(flag_content, filename="flag.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # 添加一些正常内容
    c.drawString(100, 700, "机密文档 - 请勿外传")
    c.drawString(100, 680, "公司内部使用")
    
    # 隐藏flag - 使用微小字体和与背景相似的颜色
    c.setFont("Helvetica", 2)  # 非常小的字体
    c.setFillColorRGB(0.95, 0.95, 0.95)  # 非常浅的灰色，几乎看不见
    c.drawString(10, 10, flag_content)  # 放在角落
    
    # 添加更多正常内容
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)  # 黑色
    c.drawString(100, 650, "这是一份重要文档，包含敏感信息。")
    c.drawString(100, 630, "任何未经授权的分发都将被追查。")
    
    c.save()
    print(f"已创建包含flag的PDF: {filename}")

# 从ILearn获取你的Flag 1
flag1 = "982665c425f774ce9331772148a"  # 替换为实际的Flag 1
create_flag_pdf(flag1)
