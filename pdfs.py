from xhtml2pdf import pisa
from StringIO import StringIO

def create_pdf(pdf_data):
  pdf = StringIO()
  pisa.CreatePDF(StringIO(pdf_data), pdf)
  return pdf