
def groupbyseller(trades):
    ret_ls = []
    store = {}
    helper = 0
    for trade in trades:
        if trade['seller']['id'] in store.keys():
            store[trade['seller']['id']]['products'] \
                .append({'trade_id': trade['id'], 'product': trade['product']})
            store[trade['seller']['id']]['payinfo']['total'] += trade['product']['price']

            helper += 1  # 한번 else 부터 갔다 들어오기 때문에 첫번째 들어왔을 때 뺴줌.
            # if helper == 1:
            #     store[trade['seller']['id']]['payinfo']['lack_amount'] -= trade['product']['discounted_price']
            #     store[trade['seller']['id']]['payinfo']['lack_volume'] -= 1

            # if store[trade['seller']['id']]['payinfo']['lack_amount'] > 0:  # 가격할인정책에서 남은 가격이 0원보다 클 때
            #     store[trade['seller']['id']]['payinfo']['lack_amount'] -= trade['product']['discounted_price']
            # elif store[trade['seller']['id']]['payinfo']['delivery_charge'] > 0 and trade['payinfo']['active_amount']:
            #     store[trade['seller']['id']]['payinfo']['delivery_charge'] = 0
            #
            # if store[trade['seller']['id']]['payinfo']['lack_volume'] > 0:  # 수량할인정책에서 남은 개수가 0개보다 클 때
            #     store[trade['seller']['id']]['payinfo']['lack_volume'] -= 1
            # elif store[trade['seller']['id']]['payinfo']['delivery_charge'] > 0 and trade['payinfo']['active_volume']:
            #     store[trade['seller']['id']]['payinfo']['delivery_charge'] = 0

        else:
            # lack_amount = d['payinfo']['amount'] - d['product']['discounted_price']
            # lack_volume = d['payinfo']['volume'] - 1

            # if lack_amount <= 0 and d['payinfo']['active_amount']:
            #     delivery_charge = 0
            # elif lack_volume <= 0 and d['payinfo']['active_volume']:
            #     delivery_charge = 0
            # else:
            delivery_charge = trade['payinfo']['general']
            mountain_delivery_charge = trade['payinfo']['mountain']

            store[trade['seller']['id']] = {
                'seller': trade['seller'],
                'products': [{'trade_id': trade['id'], 'product': trade['product'], 'status': trade['status']}],
                'payinfo': {
                    'total': trade['product']['price'],
                    'delivery_charge': delivery_charge,
                    'mountain_delivery_charge': mountain_delivery_charge,
                    # 'active_amount': d['payinfo']['active_amount'],
                    # 'active_volume': d['payinfo']['active_volume'],
                    # 'lack_amount': lack_amount,
                    # 'lack_volume': lack_volume
                }
            }
    for key in store:
        ret_ls.append(store[key])
    return ret_ls
