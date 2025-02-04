try:
    from __main__ import app
except ImportError:
    from main import app
    
import time
import json
import datetime                   as dt
import src.tools.repositories     as repositories

from flask                        import request
from datetime                     import datetime
from src.tools.action.dbGet       import getMysqlConn_cdk
from src.tools.action.calMuipSign import calMuipSign
from src.tools.action.dateConvert import datetime_to_timestamp, timestamp_to_datetime
from src.tools.action.rsaDecrypt  import authkey
from src.tools.loadconfig         import loadConfig
from src.tools.response           import jsonRspCommon
from src.tools.logger.system      import logger              as sys_log
from src.tools.logger.cdkservice  import logger              as cdk_log

server_time   = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 当前服务器时间
after_30_days = datetime_to_timestamp((dt.datetime.now() + dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"))  # 计算30天后的时间-邮件过期


# =========================== 游戏内部兑换CDK功能 =========================== #
# http://localhost:21000/common/api/exchangecdk?sign_type=2&auth_appid=apicdkey&authkey_ver=1&cdkey=%25e7%259a%2584%25e6%2592%2592%25e6%2597%25a6%25e6%2592%2592%25e6%2597%25a6%25e6%2592%2592%25e6%2589%2593%25e7%25ae%2597&lang=zh-cn&device_type=pc&ext=%7b%22loc%22%3a%7b%22x%22%3a1368.5118408203125%2c%22y%22%3a200.99462890625%2c%22z%22%3a696.2749633789063%7d%2c%22platform%22%3a%22WinST%22%7d&game_version=CNRELWin2.8.0_R8589120_S8812249_D8644052&plat_type=pc&authkey=G5Cl2YLYqw9KundRSKJab6WD6x1eIkL6kGvLQYOZDtJ6KV4C%2bAXggmCAl%2fMLcJkQcI1IB2vF69SmIrjBujhz3g9QAu4AbmiXIim%2b5j3WyTmkGZz995Hk4DX9%2bh9%2b9eCPB6Of993cmBfvLBL19VcLAzcE5EVvOy24e7sVIVWn2miDRL%2bFSNXeASKCsQ%2b%2b23J4sHOfm1g4K0%2bZZlNl%2f022xtSNez2Wk6tKCiZxXcaPjmlR1Fy4uM3PF1zHJAsfBfi9cIhoPwbMjvrs5gQD6aPaebcOng%2b5QoKohDpEqjw98rB0mk7bik9CQU07CQ19X2IPClEAc455cw2awAhas1ltb7O6DmfivnsqJH7GjCRUN%2bag3Qf77YqoWHW5r9J%2bQPd63Da8ppfgLLx2JmRBqdzdfAThYd%2fSXP5LaXcXCrIXfR2Ty3Fupu6j0QdgQggUSSaqhAVI91zrCjlLcQMnQ9FpeNPmbwdXqQDVGi2d88t3TqO0nYGges9bq3w%2btcsNLwoubgFJbCQI2HlWu%2fPGhgGPlInyM300m9Pt1SITzUgbZx5WIkr5FCI%2bL3dl8G7ZWNIYJErp6AUpgl%2bVBw9d0wM5pyPXyW7oH%2bPXevB%2bT9OanzwgPgSnsfitjCkg0v8CqpagbhdQ6pC3cVy3C1Qy4UTRl3sKnCwKbbB0IRKzji0EX4IVbtovuMtfUa0eUG%2ftj5W69h1qyeKDi%2f2yCdnIV%2fSt33CBNbhTL5EWcnYKFsJMvKNlUSa7R9lpU%2fMoI0mknPeSnfVZjvI5HKCoFxBpIxNk%2f8eYNFb2YlQcM5JsfbyyLhlCrorxt66FNkXW3pBMnvwBEww50hc8MRbKLueiEjfWYwBAyAE1lTT%2bIf57tiQN2HZTga54m6hCu5jj4KdNYu%2fAM9COiFNC9qweAgXj2o9zfp%2bCy7OCYfpwNp6PM4wIJ%2f%2f9EpVE0HNmKNh9GMs5dbNeAtqxQ0BbDP7J9FGMlsWR9ugBUJXgMKQ2reXPx4PKIEyR%2b9Gn1pNQWXc3HE5z6BJtDBmHU%2fTJxHX05G2ZV8IwVTneogIdVEA5juDOMA39rGmW5KNhAC8EfWFHkoCQgtBKADfyT8FgVjg0iN%2fEC%2fety1WROb8jZ61lI4A7KQVDhHhphzlYRGwIE%2f6y5WhE1H82lbreohukMrDtE6oG51m8zrPC%2fA8K8RotTFgBW%2bs6nSK2nF2WJ59bOcVX1kr%2fr6UNvF9ogY%2bnVwX5qKxP9qoxqQ6R58I5bBpPdf4kzTy%2ftbchT%2fHgmfRFf7LP%2fWeNeqBqgqTqiEpuTFIPsTEYwYWPO64CDAJHTVA7kfhoM%2fFXYp%2fXwbJk6BosiM9OU6mIAkbLo3oDHykh0IZPfH%2feDiisGg%3d%3d&game_biz=hk4e_global
@app.route("/common/api/exchangecdk", methods=["GET"])
def cdk_verify():
    def get_request_args():
        cdkey       = request.args.get("cdkey")
        auth_key    = request.args.get("authkey")
        authkey_ver = request.args.get("authkey_ver")
        cdk_log.info(f"主机 {request.remote_addr} 客户端CDK信息: CDK: {cdkey} Authkey version: {authkey_ver} Authkey: {auth_key}")
        return cdkey, auth_key, authkey_ver

    def decrypt_auth_key(auth_key, authkey_ver):
        keys = authkey(auth_key, authkey_ver)
        message = json.loads(keys)
        cdk_log.info(f"Authkey 解密信息: {message} 原 Authkey: {auth_key}")
        return message

    def fetch_cdk_status(cdkey):
        db_name = loadConfig()['Database']['mysql']['exchcdk_library_name']
        cursor = getMysqlConn_cdk().cursor()
        cursor.execute("USE `{}`".format(db_name))
        cursor.execute("SELECT * FROM `t_cdk_redeem` WHERE `cdk_name` = %s", cdkey)
        return cursor.fetchone()

    def check_cdk_validity(cdk_status):
        if cdk_status is None:
            cdk_log.error(f"主机 {request.remote_addr} CDK兑换失败: 无效的兑换码")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "无效的兑换码")
        return None  # No error

    def get_cdk_details(cdk_status):
        keys = [
            "times",
            "enabled",
            "cdk_name",
            "open_time",
            "expire_time",
            "template_id",
        ]
        return [cdk_status.get(key) for key in keys]

    def is_cdk_expired(open_time, expire_time, current_time):
        system_time_local = timestamp_to_datetime(current_time)
        cdk_enable_time   = timestamp_to_datetime(open_time)
        cdk_disable_time  = timestamp_to_datetime(expire_time)
        cdk_log.info(f"当前CDK启用时间: {cdk_enable_time} 结束时间: {cdk_disable_time} 目标系统时间: {system_time_local}")
        if open_time > current_time:
            cdk_log.error(f"主机 {request.remote_addr} CDK兑换失败: 未启用")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "兑换码尚未启用")
        elif expire_time < current_time:
            cdk_log.error(f"主机 {request.remote_addr} CDK兑换失败: 已过期")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "兑换码已过期")
        elif enabled == 0:
            cdk_log.error(f"主机 {request.remote_addr} CDK兑换失败: 未启用")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "兑换码尚未启用")
        elif times <= 0:
            cdk_log.error(f"主机 {request.remote_addr} CDK兑换失败: 已兑换(过期)")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "兑换码已被使用")
        return None  # No error

    def has_already_redeemed(cdkey, uid):
        cursor = getMysqlConn_cdk().cursor()
        cursor.execute(
            "SELECT * FROM `t_cdk_record` WHERE `cdk_name` = %s AND `uid` = %s",
            (cdkey, uid),
        )
        return cursor.fetchone() is not None

    def fetch_mail_template(template_id):
        cursor = getMysqlConn_cdk().cursor()
        cursor.execute("SELECT * FROM `t_cdk_template` WHERE `cdk_template_id` = %s", template_id)
        return cursor.fetchone()

    def send_mail(uid, templates):
        expire_time    = after_30_days
        title          = templates.get("title")
        sender         = templates.get("sender")
        content        = templates.get("content")
        item_list      = templates.get("item_list")
        importance     = templates.get("importance")
        is_collectible = templates.get("is_collectible")
        
        region = loadConfig()["Muipserver"]["region"]
        content = (
            f"title={title}&sender={sender}&content={content}"
            + f"&expire_time={expire_time}&importance={importance}"
            + f"&is_collectible={is_collectible}&item_list={item_list}"
            + f"&region={region}"
        )
        # 命令构造 直接传入 calMuipSign
        command = (
            f"cmd=1005&uid={uid}&{content}"
            + "&ticket=COKESERVER@"
            + str(time.mktime(datetime.now().timetuple())).split(".")[0]
        )
        cdk_log.info(f"构造 URL 并尝试发送到目标 muipserver: {command}")
        return calMuipSign(command)

    def insert_redeem_record(cdk_name, uid, account_type, account_uid, region, game, platform_type, server_time,):
        cursor = getMysqlConn_cdk().cursor()
        cursor.execute(
            "INSERT INTO `t_cdk_record` (`cdk_name`, `uid`, `account_type`, `account_uid`,`region`, `game`, `platform`, `used_time`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
            (
                cdk_name,
                uid,
                account_type,
                account_uid,
                region,
                game,
                platform_type,
                server_time,
            ),
        )

    def update_cdk_times(cdk_name, times):
        cursor = getMysqlConn_cdk().cursor()
        cursor.execute("UPDATE t_cdk_redeem SET times = %s WHERE cdk_name = %s", (times, cdk_name))

    if not request.args:
        sys_log.error(f"主机 {request.remote_addr} CDK功能交互失败: 缺少所配置的基本参数")
        return jsonRspCommon(repositories.RES_FAIL,"环境错误")

    # 保证基本参数
    required_params = ['cdkey','sign_type', 'auth_appid', 'authkey_ver','authkey']
    if not all(param in request.args for param in required_params):
        sys_log.error(f"主机 {request.remote_addr} CDK功能交互失败: 缺少所配置的基本参数")
        return jsonRspCommon(repositories.RES_FAIL,"参数错误")

    # 如果启用CDK
    if loadConfig()["Setting"]["cdkexchange"]:
        cdkey, auth_key, authkey_ver = get_request_args()
        
        # 尝试解密
        try:
            message = decrypt_auth_key(auth_key, authkey_ver)
        except Exception:
            sys_log.error(f"主机 {request.remote_addr} CDK功能交互失败: 无法解密 Authkey")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "系统错误")

        uid           = message.get("uid")
        game          = message.get("game")
        region        = message.get("region")
        account_uid   = message.get("account_uid")
        account_type  = message.get("ext").get("account_type")
        platform_type = message.get("ext").get("platform_type")

        cdk_status = fetch_cdk_status(cdkey)
        error = check_cdk_validity(cdk_status)
        if error:
            return error

        times, enabled, cdk_name, open_time, expire_time, template_id = get_cdk_details(cdk_status)
        current_time = datetime_to_timestamp(server_time)
        open_time    = datetime_to_timestamp(open_time)
        expire_time  = datetime_to_timestamp(expire_time)
        cdk_expired  = is_cdk_expired(open_time, expire_time, current_time)
        if cdk_expired:
            return cdk_expired

        if has_already_redeemed(cdkey, uid):
            sys_log.error(f"主机 {request.remote_addr} CDK功能交互失败: CDK已兑换 UID: {uid} 区域: {region} 平台类型 {game}")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "你已经兑换过这个CDK了")

        templates = fetch_mail_template(template_id)
        if templates is None:
            sys_log.error(f"主机 {request.remote_addr} CDK功能交互失败: 模板文件缺失 UID: {uid} 区域: {region} 平台类型 {game}")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "邮件模板不存在！兑换码发送失败")

        # 检查是否发送成功
        response = json.loads(send_mail(uid, templates))
        if response['msg'] == "loading muipserver failed":
            sys_log.error(f"主机 {request.remote_addr} CDK功能交互失败: 邮件配置异常  UID: {uid} 区域: {region} 平台类型 {game}")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "邮件功能错误！兑换码发送失败")
        
        if response['msg'] == "verify sign error":
            sys_log.error(f"主机 {request.remote_addr} CDK功能交互失败: muipserver 签名错误  UID: {uid} 区域: {region} 平台类型 {game}")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "奖励物品发送失败，请联系管理员")
        
        if response['msg'] == "succ":
            insert_redeem_record(
                cdk_name,
                uid,
                account_type,
                account_uid,
                region,
                game,
                platform_type,
                server_time,
            )

            times -= 1
            update_cdk_times(cdk_name, times)
            cdk_log.info(f"主机 {request.remote_addr} CDK兑换成功: UID: {uid} 使用的CDK: {cdk_name} 区域: {region} 平台类型: {game}")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_SUCC, {})
        else:
            sys_log.error(f"CDK功能交互失败: 未能成功发送邮件  UID: {uid} 区域: {region} 平台类型 {game}")
            return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "系统错误，请联系管理员")
    else:
        sys_log.error(f"CDK功能交互失败: 功能已关闭  UID: {uid} 区域: {region} 平台类型 {game}")
        return jsonRspCommon(repositories.RES_CDK_EXCHANGE_FAIL, "邮件系统已关闭")
