import scribus

scribus.openDoc('Test.sla')
pdf = scribus.PDFfile()
pdf.file = 'result.pdf'
pdf.save()