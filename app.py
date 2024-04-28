import streamlit as st
import pulp
from mip import Model, xsum, minimize, BINARY, INTEGER


def calculate_mip(balances, time_limit=30):
    # 人物のリスト
    people = list(balances.keys())

    # 問題のインスタンスを作成
    prob = Model("Minimize_Transactions")

    # 取引変数を作成（各人物のペアごとに1つの変数）
    transactions = {(i, j): prob.add_var(var_type=INTEGER, name=f"Transaction_{i}_{j}") for i in people for j in people}

    # 取引が発生するかどうかを表すバイナリ変数
    transaction_occurs = {(i, j): prob.add_var(var_type=BINARY, name=f"Transaction_Occurs_{i}_{j}") for i in people for j in people}

    # 目的関数を設定（取引回数の合計を最小化）
    prob.objective = minimize(xsum(transaction_occurs[i, j] for i in people for j in people if i != j))

    # 制約を追加（各人物のポイントバランスが0になるように）
    for person in people:
        prob += xsum(transactions[i, person] for i in people if i != person) - \
                xsum(transactions[person, j] for j in people if j != person) == balances[person]

    for i in people:
        for j in people:
            if i != j:
                # 取引量が正であることを保証するための大きな定数 M
                M = sum(abs(b) for b in balances.values())
                prob += transactions[i, j] <= M * transaction_occurs[i, j]
                prob += transactions[i, j] >= 0

    # 問題を解く
    prob.optimize(max_seconds=time_limit)

    result = []

    # 結果を表示
    print("取引の最適解:")
    for i in people:
        for j in people:
            if i != j and transactions[i, j].x > 0:
                print(f"{i} から {j} への移動: {transactions[i, j].x} ポイント")
                result.append({"From": i, "To": j, "Point": transactions[i, j].x})
    return result


def calculate_pulp(balances, time_limit):
    # 人物のリスト
    people = list(balances.keys())

    # 問題のインスタンスを作成
    prob = pulp.LpProblem("Minimize_Transactions", pulp.LpMinimize)

    # 取引変数を作成（各人物のペアごとに1つの変数）
    transactions = pulp.LpVariable.dicts("Transaction", (people, people), 0, None, pulp.LpInteger)

    # 取引が発生するかどうかを表すバイナリ変数
    transaction_occurs = pulp.LpVariable.dicts("Transaction_Occurs", (people, people), 0, 1, cat=pulp.LpBinary)

    # 目的関数を設定（取引回数の合計を最小化）
    prob += pulp.lpSum(transaction_occurs[i][j] for i in people for j in people if i != j)

    # 制約を追加（各人物のポイントバランスが0になるように）
    for person in people:
        prob += pulp.lpSum(transactions[i][person] for i in people if i != person) - \
                pulp.lpSum(transactions[person][j] for j in people if j != person) == balances[person]
    
    for i in people:
        for j in people:
            if i != j:
                # 取引量が正であることを保証するための大きな定数 M
                M = sum(abs(b) for b in balances.values())
                prob += transactions[i][j] <= M * transaction_occurs[i][j]
                prob += transactions[i][j] >= 0

    # 問題を解く
    prob.solve(pulp.PULP_CBC_CMD(timeLimit=time_limit))

    result = []

    # 結果を表示
    print("取引の最適解:")
    for i in people:
        for j in people:
            if i != j and transactions[i][j].varValue > 0:
                print(f"{i} から {j} への移動: {transactions[i][j].varValue} ポイント")
                result.append({"From": i, "To": j, "Point": transactions[i][j].varValue})
    return result

def main():
    # UI部分をStreamlitで再現
    st.title("ポイント精算")

    with st.sidebar:
        num = st.number_input("人数", min_value=3, max_value=30, value=3, step=1)
        time_limit = st.number_input("計算時間の上限[sec]", min_value=5, max_value=600, value=30, step=1)
        library = st.selectbox("ライブラリ", ["PuLP", "MIP"])


    # 初期の入力フィールドを追加
    balances = {}
    balance = 0
    for i in range(num):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(f"名前{i+1}", value=chr(ord("A")+i))
        with col2:
            point = st.number_input(f"ポイント{i+1}", value=0, step=1)
        balances[name] = point
        balance += point


    # 計算ボタン
    if st.button("計算"):
        # 計算結果を表示
        if balance == 0:
            if library == "PuLP":
                result = calculate_pulp(balances, time_limit=time_limit)
            else:
                result = calculate_mip(balances, time_limit=time_limit)
            st.write("結果")
            for r in result:
                st.write(f"{r['From']} から {r['To']} への移動: {int(r['Point'])}pt")
        else:
            st.write(f"{balance}ptずれがあります。")


if __name__ == "__main__":
    main()
