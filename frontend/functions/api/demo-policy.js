import orders from './demo-orders.js'

export const issues = ['order', 'missing', 'damaged', 'return', 'refund', 'partner', 'human']
export const exampleOrders = orders

export function extractOrderId(message) {
  return message.match(/\bKV-\d{5}\b/i)?.[0].toUpperCase() ?? null
}

export function classify(message) {
  const text = message.toLowerCase()
  const patterns = [
    ['human', ['medewerker', 'persoon spreken', 'mens spreken', 'klantenservice']],
    ['damaged', ['beschadig', 'beschadgt', 'kapot', 'stuk aangekomen', 'lekkage']],
    [
      'missing',
      ['ontbreek', 'ontbrekt', 'mist een', 'niet compleet', 'mis een artikel', 'mis een artkel'],
    ],
    ['refund', ['terugbetaling', 'geld terug', 'refund']],
    ['partner', ['partner', 'externe verkoper']],
    ['return', ['retour', 'terugsturen', 'terugbrengen']],
    ['order', ['bestelling', 'order', 'pakket', 'bezorg', 'levering']],
  ]
  return patterns.find(([, words]) => words.some((word) => text.includes(word)))?.[0] ?? null
}

export function advice(order, issue) {
  if (order.partner_order)
    return [
      'Dit is een partnerbestelling. De retourroute kan afwijken; controleer de instructies bij de verkooppartner. Een medewerker kan de situatie beoordelen.',
      true,
      'Partnerprocedure vereist beoordeling',
    ]
  if (issue === 'missing') {
    const missing = order.items
      .filter((item) => item.quantity_delivered < item.quantity_ordered)
      .map((item) => item.name)
    if (
      missing.length &&
      (order.delivery_status.includes('tweede pakket') ||
        order.delivery_status.includes('onderweg'))
    )
      return [
        'Deze voorbeeldorder heeft nog een zending onderweg. Controleer eerst de tweede levering; als die niet aankomt, kan een medewerker dit onderzoeken.',
        false,
        '',
      ]
    if (missing.length)
      return [
        `Volgens de voorbeeldorder ontbreekt: ${missing.join(', ')}. Bewaar de pakbon en verpakking. Een medewerker moet de levering onderzoeken.`,
        true,
        'Ontbrekend artikel vereist orderonderzoek',
      ]
    return [
      'Deze voorbeeldorder toont geen ontbrekend artikel. Als je toch iets mist, kan een medewerker de levering onderzoeken.',
      true,
      'Klant meldt afwijking van ordergegevens',
    ]
  }
  if (issue === 'damaged')
    return [
      "Bewaar het artikel en de verpakking. Maak indien mogelijk foto's van de schade. Een medewerker beoordeelt de passende oplossing; er is nog geen vergoeding toegezegd.",
      true,
      'Schade vereist menselijke beoordeling',
    ]
  if (issue === 'refund')
    return [
      `De geregistreerde terugbetalingsstatus is: ${order.refund_status}. Dit is een simulatie; ik kan geen betaling starten of datum toezeggen.`,
      false,
      '',
    ]
  if (issue === 'return') {
    if (order.return_eligible === true)
      return [
        'Volgens de vereenvoudigde demo-regel lijkt dit artikel retourneerbaar. Controleer vóór verzending de actuele voorwaarden en artikeluitzonderingen.',
        false,
        '',
      ]
    if (order.return_eligible === false)
      return [
        'De demo-regel markeert dit artikel als niet direct retourneerbaar. Een medewerker kan de reden en je rechten beoordelen.',
        true,
        'Retouruitzondering vereist beoordeling',
      ]
    return [
      'De retourmogelijkheid is onzeker. Een medewerker kan de toepasselijke voorwaarden beoordelen.',
      true,
      'Retourvoorwaarden onzeker',
    ]
  }
  if (issue === 'human')
    return [
      'Ik zet de context klaar voor een medewerker van deze demonstratie. Er vindt geen echte overdracht naar Kruidvat plaats.',
      true,
      'Klant vraagt om menselijke ondersteuning',
    ]
  return [
    `De voorbeeldbestelling heeft status ‘${order.status}’ en bezorgstatus ‘${order.delivery_status}’. Bekijk de orderkaart voor artikelen en vervolgstappen.`,
    false,
    '',
  ]
}
