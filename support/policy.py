import re
from .models import Issue, Order

ORDER_PATTERN = re.compile(r"\bKV-\d{5}\b", re.IGNORECASE)


def extract_order_id(message: str) -> str | None:
    match = ORDER_PATTERN.search(message)
    return match.group().upper() if match else None


def classify(message: str) -> Issue | None:
    text = message.lower()
    patterns = [
        ("human", ("medewerker", "persoon spreken", "mens spreken", "klantenservice")),
        ("damaged", ("beschadig", "beschadgt", "kapot", "stuk aangekomen", "lekkage")),
        ("missing", ("ontbreek", "ontbrekt", "mist een", "niet compleet", "mis een artikel", "mis een artkel")),
        ("refund", ("terugbetaling", "geld terug", "refund")),
        ("partner", ("partner", "externe verkoper")),
        ("return", ("retour", "terugsturen", "terugbrengen")),
        ("order", ("bestelling", "order", "pakket", "bezorg", "levering")),
    ]
    return next((issue for issue, words in patterns if any(word in text for word in words)), None)


def advice(order: Order, issue: Issue) -> tuple[str, bool, str]:
    if order.partner_order:
        return ("Dit is een partnerbestelling. De retourroute kan afwijken; controleer de instructies bij de verkooppartner. Een medewerker kan de situatie beoordelen.", True, "Partnerprocedure vereist beoordeling")
    if issue == "missing":
        missing = [item.name for item in order.items if item.quantity_delivered < item.quantity_ordered]
        if missing and ("tweede pakket" in order.delivery_status or "onderweg" in order.delivery_status):
            return ("Deze voorbeeldorder heeft nog een zending onderweg. Controleer eerst de tweede levering; als die niet aankomt, kan een medewerker dit onderzoeken.", False, "")
        if missing:
            return (f"Volgens de voorbeeldorder ontbreekt: {', '.join(missing)}. Bewaar de pakbon en verpakking. Een medewerker moet de levering onderzoeken.", True, "Ontbrekend artikel vereist orderonderzoek")
        return ("Deze voorbeeldorder toont geen ontbrekend artikel. Als je toch iets mist, kan een medewerker de levering onderzoeken.", True, "Klant meldt afwijking van ordergegevens")
    if issue == "damaged":
        return ("Bewaar het artikel en de verpakking. Maak indien mogelijk foto's van de schade. Een medewerker beoordeelt de passende oplossing; er is nog geen vergoeding toegezegd.", True, "Schade vereist menselijke beoordeling")
    if issue == "refund":
        return (f"De geregistreerde terugbetalingsstatus is: {order.refund_status}. Dit is een simulatie; ik kan geen betaling starten of datum toezeggen.", False, "")
    if issue == "return":
        if order.return_eligible is True:
            return ("Volgens de vereenvoudigde demo-regel lijkt dit artikel retourneerbaar. Controleer vóór verzending de actuele voorwaarden en artikeluitzonderingen.", False, "")
        if order.return_eligible is False:
            return ("De demo-regel markeert dit artikel als niet direct retourneerbaar. Een medewerker kan de reden en je rechten beoordelen.", True, "Retouruitzondering vereist beoordeling")
        return ("De retourmogelijkheid is onzeker. Een medewerker kan de toepasselijke voorwaarden beoordelen.", True, "Retourvoorwaarden onzeker")
    if issue == "human":
        return ("Ik zet de context klaar voor een medewerker van deze demonstratie. Er vindt geen echte overdracht naar Kruidvat plaats.", True, "Klant vraagt om menselijke ondersteuning")
    return (f"De voorbeeldbestelling heeft status ‘{order.status}’ en bezorgstatus ‘{order.delivery_status}’. Bekijk de orderkaart voor artikelen en vervolgstappen.", False, "")
