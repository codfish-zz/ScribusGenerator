import scribus

scribus.openDoc('test.sla')
pdf = scribus.PDFfile()
pdf.file = 'result.pdf'
pdf.save()