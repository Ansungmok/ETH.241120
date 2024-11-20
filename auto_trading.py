import pyupbit
import time
from datetime import datetime

# Upbit API 키 설정 (개인 API 키 입력)
ACCESS_KEY = "uKpCOPJ910TPxLxAj0CxnxPdZqJhMFX0Hkhu1Nit"
SECRET_KEY = "rxSnFDxeSX96Y1x2N4G59JxNH1AY2Ncw37bx8xxP"

# Upbit 객체 생성
upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

# 알림 함수
def notify(message):
    print(f"[알림] {message}")

# 주문 체결가 확인 함수
def get_filled_price(order_uuid):
    try:
        order_info = upbit.get_order(order_uuid)
        # 체결된 가격 정보 가져오기
        if order_info['state'] == 'done':  # 주문이 체결된 경우
            trades = order_info['trades']  # 체결된 거래 정보
            if trades:
                return float(trades[0]['price'])  # 체결가 반환
        return None
    except Exception as e:
        notify(f"체결가 확인 오류: {e}")
        return None

# ETH 매수/매도 함수
def auto_trade():
    try:
        # 전일 저가 확인
        ticker = "KRW-ETH"
        ticker_data = pyupbit.get_ohlcv(ticker, interval="day", count=2)
        yesterday_low = ticker_data.iloc[-2]['low']

        # 현재 가격 확인
        current_price = pyupbit.get_current_price(ticker)

        # ETH 잔고 확인
        balance = upbit.get_balance(ticker)
        orders = upbit.get_order(ticker)  # 기존 주문 확인

        # 매수 조건: ETH 잔고가 없고, 현재가격 <= 전일 저가
        if balance == 0 and not orders:
            notify(f"매수 주문 진행 중: 전일저가 {yesterday_low}로 1 ETH 매수")
            buy_order = upbit.buy_limit_order(ticker, yesterday_low, 1)
            notify(f"매수 주문 완료: 주문 ID - {buy_order['uuid']}")
            if buy_order:
                notify("매수 주문 생성 완료, 체결 대기 중...")
                # 체결가 확인
                time.sleep(5)  # 체결 대기 (5초)
                filled_price = get_filled_price(buy_order['uuid'])
                if filled_price:
                    notify(f"매수 체결 완료: 체결가 - {filled_price}")
                else:
                    notify("매수 체결 실패: 체결가 확인 불가")
            else:
                notify("매수 주문 생성 실패")            

        # 매도 조건: ETH 잔고가 있을 경우
        elif balance:
            avg_buy_price = float(upbit.get_avg_buy_price(ticker))  # 평균 매수가
            target_price = avg_buy_price + 100000  # 매수가 + 100,000원
            new_target_price = yesterday_low + 100000  # 전일 저가 + 100,000원

            # 기존 매도 주문 확인 및 처리
            for order in orders:
                if order['side'] == 'ask':  # 매도 주문만 확인
                    order_price = float(order['price'])
                    if order_price != new_target_price:
                        upbit.cancel_order(order['uuid'])
                        notify(f"기존 매도 주문 취소: 주문 ID - {order['uuid']} (기존 가격: {order_price}, 새 가격: {new_target_price})")
                    else:
                        notify(f"기존 매도 주문 유지: 주문 ID - {order['uuid']} (가격: {order_price})")
                        return  # 기존 주문 유지 시 함수 종료

            # 새로운 매도 주문 생성
            notify(f"매도 주문 진행 중: {target_price}에 1 ETH 매도")
            sell_order = upbit.sell_limit_order(ticker, target_price, balance)
            notify(f"매도 주문 완료: 주문 ID - {sell_order['uuid']}")

        # 패스 조건: ETH 주문이 설정되어 있는 경우
        else:
            for order in orders:
                if order['side'] == 'ask':  # 매도 주문만 확인
                    order_price = float(order['price'])
                    notify(f"기존 매도 주문 유지. 가격: {order_price}, 손익: {order_price-current_price}")
                else:
                    order_price = float(order['price'])
                    notify(f"기존 매수 주문 유지. 가격: {order_price}")


    except Exception as e:
        notify(f"오류 발생: {e}")

# 프로그램 시작
if __name__ == "__main__":
    notify("프로그램 실행 - 자동 매매 시작")
    while True:
        auto_trade()
        notify("10분 후 프로그램을 다시 실행합니다.")
        time.sleep(600)  # 10분 대기
