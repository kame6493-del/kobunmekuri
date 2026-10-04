/**
 * 課金の設定(RevenueCat)。
 * - 商品は買い切り(非消耗型)1つ: 本編の全語・例文モード・敬語セット・助動詞セットがまとめて開く
 * - キーは RevenueCat の「公開」APIキー(アプリに埋め込む物で秘密ではない)。まだ無いので空。空のあいだは「購入は準備中」と出す
 */
export const BILLING = {
  productId: 'jp.kobunmekuri.app.full',
  entitlement: 'full',
  /** ストアで付ける値段(画面の文言用。実際の表示はストアから取った値を優先) */
  price: '¥610',
  revenuecat: { ios: 'appl_BwkRXsaTGnmZqVnLEKQofatGAWB', android: 'goog_alhXNGTbGKZunMEgasLOAseyrCv' },
};

export const APP = {
  name: 'こぶんめくり',
  /** サポートとプライバシーポリシーの置き場所(公開したら入れる) */
  site: '',
};
