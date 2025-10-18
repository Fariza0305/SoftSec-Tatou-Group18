#!/usr/bin/env python3
import requests
import json
import os
import sys
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# API配置
BASE_URL = "http://localhost:5000"  # 根据实际情况调整
USERNAME = "Mr_Important"
PASSWORD = "Aaimportant.123"
EMAIL = "important@163.com"
FLAG = "b9aa48abdd8542486599a7bcd454256402eb99e4"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.document_id = None
        
    def create_test_pdf(self):
        """创建测试PDF文件"""
        print("📄 创建测试PDF文件...")
        
        # 创建PDF内容
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # 添加一些文本内容
        c.drawString(100, 750, "Test Document for Watermarking")
        c.drawString(100, 700, "This is a test document to verify watermarking functionality.")
        c.drawString(100, 650, "Document ID: TEST-001")
        c.drawString(100, 600, "Created by: API Tester")
        
        c.save()
        buffer.seek(0)
        
        # 保存到文件
        pdf_path = "/tmp/test_document.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        print(f"✅ PDF文件已创建: {pdf_path}")
        return pdf_path
    
    def login(self):
        """步骤1: 使用用户名密码登录获取token"""
        print("🔐 步骤1: 登录获取token...")
        
        login_data = {
            "email": EMAIL,
            "password": PASSWORD
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/api/login", json=login_data)
            print(f"登录响应状态码: {response.status_code}")
            print(f"登录响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                print(f"✅ 登录成功，获得token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ 登录失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return False
    
    def upload_document(self, pdf_path):
        """步骤3: 上传PDF文档"""
        print("📤 步骤3: 上传PDF文档...")
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': ('test_document.pdf', f, 'application/pdf')}
                headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
                
                response = self.session.post(
                    f"{BASE_URL}/api/upload-document",
                    files=files,
                    headers=headers
                )
                
            print(f"上传响应状态码: {response.status_code}")
            print(f"上传响应内容: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.document_id = result.get('id') or result.get('document_id')
                print(f"✅ 文档上传成功，文档ID: {self.document_id}")
                return True
            else:
                print(f"❌ 文档上传失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 上传异常: {str(e)}")
            return False
    
    def create_watermark(self):
        """步骤4: 创建带flag的水印"""
        print("🎨 步骤4: 创建带flag的水印...")
        
        timestamp = int(time.time())
        watermark_data = {
            "method": "attachment",
            "intended_for": f"test_{timestamp}",
            "secret": FLAG,
            "key": "test_key"
        }
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/create-watermark/{self.document_id}",
                json=watermark_data,
                headers=headers
            )
            
            print(f"创建水印响应状态码: {response.status_code}")
            print(f"创建水印响应内容: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ 水印创建成功: {result}")
                return True
            else:
                print(f"❌ 水印创建失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 创建水印异常: {str(e)}")
            return False
    
    def download_document(self):
        """步骤5: 下载水印PDF"""
        print("📥 步骤5: 下载水印PDF...")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
            
            response = self.session.get(
                f"{BASE_URL}/api/get-document/{self.document_id}",
                headers=headers
            )
            
            print(f"下载响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 保存下载的PDF
                download_path = f"/tmp/watermarked_document_{self.document_id}.pdf"
                with open(download_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ 水印PDF下载成功: {download_path}")
                print(f"文件大小: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ 下载失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 下载异常: {str(e)}")
            return False
    
    def read_watermark(self):
        """步骤6: 读取水印内容"""
        print("🔍 步骤6: 读取水印内容...")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            read_data = {
                "method": "attachment",
                "key": "test_key"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/read-watermark/{self.document_id}",
                json=read_data,
                headers=headers
            )
            
            print(f"读取水印响应状态码: {response.status_code}")
            print(f"读取水印响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 水印读取成功: {result}")
                return True
            else:
                print(f"❌ 水印读取失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 读取水印异常: {str(e)}")
            return False
    
    def list_documents(self):
        """步骤7: 列出所有文档"""
        print("📋 步骤7: 列出所有文档...")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
            
            response = self.session.get(
                f"{BASE_URL}/api/list-documents",
                headers=headers
            )
            
            print(f"列出文档响应状态码: {response.status_code}")
            print(f"列出文档响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 文档列表获取成功: {result}")
                return True
            else:
                print(f"❌ 文档列表获取失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 列出文档异常: {str(e)}")
            return False
    
    def run_test(self):
        """运行完整测试流程"""
        print("🚀 开始API测试流程...")
        print(f"目标Flag: {FLAG}")
        print(f"用户名: {USERNAME}")
        print(f"API基础URL: {BASE_URL}")
        print("-" * 50)
        
        # 步骤1: 登录
        if not self.login():
            print("❌ 登录失败，终止测试")
            return False
        
        # 步骤2: 创建PDF
        pdf_path = self.create_test_pdf()
        
        # 步骤3: 上传PDF
        if not self.upload_document(pdf_path):
            print("❌ 上传失败，终止测试")
            return False
        
        # 步骤4: 创建水印
        if not self.create_watermark():
            print("❌ 创建水印失败，终止测试")
            return False
        
        # 步骤5: 下载PDF
        if not self.download_document():
            print("❌ 下载失败，终止测试")
            return False
        
        # 步骤6: 读取水印
        self.read_watermark()  # 即使失败也继续测试
        
        # 步骤7: 列出文档
        if not self.list_documents():
            print("❌ 列出文档失败，终止测试")
            return False
        
        print("-" * 50)
        print("🎉 所有测试步骤完成！")
        return True

if __name__ == "__main__":
    tester = APITester()
    tester.run_test()
