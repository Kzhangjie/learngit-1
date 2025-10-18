import utils.constants as constants
import airsheet
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


def get_df(file_id, sheet_name, wps_sid=constants.WPS_SID, drop_na=True):
    airsheet.init(file_id=file_id, wps_sid=wps_sid, sheet_name=sheet_name)
    df = airsheet.xl("A:FZ", headers=True, sheet_name=[sheet_name])
    if drop_na:
        df = df.dropna(axis=1, how="all")  # type: ignore
    df.fillna("", inplace=True)  # type: ignore
    return df
