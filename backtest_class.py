@dataclass
class Position:
    #time: str
    price: float
    stop_loss: float # price(1-sl)
    take_profit: float # price(1+tp)
    n_shares: int
    #type: str

def backtest(data, sl, tp, n_shares) -> list[float]:
    data = data.copy()
    # define constraints, iterables and globals

    for i, row in data.iterrows():
        # close positions
        for pos in active_long.copy():
            if (pos.sl > row.close) or (pos.tp < row.close):
                cash += pos.n_shares * row.close * (1 - com) # sin 1-com para saccar el valor del portafolio en ese momento
                active_long.remove(pos)

        # short positions
        for pos in active_short.copy():
            if (pos.tp > row.close) or (pos.sl < row.close):
                cash += (pos.price * pos.n_shares) + (pos.price - row.close) * pos.n_shares * (1 - com)
                active_short.remove(pos)

        # open new positions

        # long
        if row.BUY_SIG:
            cost = row.close * n_shares * (1 + com)
            if cash > cost:
                cash -= cost
                active_long.append(
                    Position(
                        price=row.close,
                        stop_loss=row.close * (1 - sl),
                        take_profit=row.close * (1 + tp),
                        n_shares=n_shares
                    )
                )
        # short
        if row.SELL_SIG:
            cost = row.close * n_shares * (1 + com)
            if cash > cost:
                cash -= cost
                active_short.append(
                    Position(
                        price=row.close,
                        stop_loss=row.close * (1 + sl),
                        take_profit=row.close * (1 - tp),
                        n_shares=n_shares
                    )
                )  

        # portfolio value
        port_value += cash
        for pos in active_long:
            port_value += pos.n_shares * row.close
        for pos in active_short:
            port_value += (pos.price * pos.n_shares) + (pos.price - row.close) * pos.n_shares 

    port_hist.append(port_value)

    # todo: sell

    return port_hist       


def optimize(trial, train_data) -> float:
    data = train_data.copy()
    # trial.suggest params
    n_splits = 5
    calmars = []
    len_data = len(data)

    for i in range(n_splits):
        size = len_data//n_splits
        start_idx = i * size
        end_idx = (i + 1) * size

        chunk = data.iloc[start_idx:end_idx, :]
        port_vals = backtest(chunk, sl, tp, n_shares)
        calmar = get_calmar(port_vals)
        calmars.append(calmar)

    return np.mean(calmars)


# en el main

study = optuna.create_study(direction='maximize')
study.optimize(lambda trial: optimize(trial, train_data), n_trials=100)
study.best_params # el profe puso best_study