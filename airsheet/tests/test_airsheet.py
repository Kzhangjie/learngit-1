import airsheet_sdk.airsheet as airsheet

wps_sid = "x"
file_id = "259210293537"
sheet_name = "工作表1"

airsheet.init(wps_sid=wps_sid,
              file_id=file_id,
              sheet_name=sheet_name)

# df = xl()

data = [x for x in range(10)]
airsheet.write_xl(data, start_row=20, start_column=0)
