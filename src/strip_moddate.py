import pikepdf

def fully_strip_dates(input_path, output_path):
    with pikepdf.open(input_path) as pdf:
        
        # 1. Remove standard /ModDate and /CreationDate from DocInfo
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            #meta['pdf:Producer'] = "@MADE BY RAYIN"
            if 'xmp:ModifyDate' in meta:
                del meta['xmp:ModifyDate']

        # 2. Clear the legacy Info dictionary (handles /ModDate)
        if "/Info" in pdf.trailer:
            del pdf.trailer["/Info"]

        # 3. Save the PDF (preserves original version)
        pdf.save(output_path, fix_metadata_version=False)

fully_strip_dates("1.pdf", "2.pdf")
