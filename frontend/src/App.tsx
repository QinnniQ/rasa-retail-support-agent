import { useEffect, useRef, useState } from 'react'
import {
  ArrowRight,
  ArrowUpRight,
  Box,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  Headphones,
  HeartHandshake,
  Menu,
  MessageCircle,
  Package,
  PackageCheck,
  RotateCcw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Truck,
  Workflow,
  X,
} from 'lucide-react'
import { api, type Case, type Issue, type Order, type Reply, type Status, type Trace } from './api'

const categories: {
  id: Issue
  title: string
  description: string
  icon: typeof Package
  prompt: string
  example: string
}[] = [
  {
    id: 'order',
    title: 'Bestelling volgen',
    description: 'Bekijk status en bezorging',
    icon: Truck,
    prompt: 'Ik wil mijn bestelling volgen',
    example: 'KV-30014',
  },
  {
    id: 'return',
    title: 'Retourneren',
    description: 'Ontdek je mogelijkheden',
    icon: RotateCcw,
    prompt: 'Kan ik mijn bestelling retourneren?',
    example: 'KV-60047',
  },
  {
    id: 'damaged',
    title: 'Beschadigd artikel',
    description: 'Hulp bij schade',
    icon: HeartHandshake,
    prompt: 'Mijn artikel is beschadigd aangekomen',
    example: 'KV-20991',
  },
  {
    id: 'missing',
    title: 'Ontbrekend artikel',
    description: 'Een artikel niet ontvangen?',
    icon: Package,
    prompt: 'Er ontbreekt een artikel in mijn bestelling',
    example: 'KV-10482',
  },
  {
    id: 'refund',
    title: 'Terugbetaling',
    description: 'Controleer de status',
    icon: PackageCheck,
    prompt: 'Wat is de status van mijn terugbetaling?',
    example: 'KV-50036',
  },
  {
    id: 'human',
    title: 'Contact met medewerker',
    description: 'Zet je vraag door',
    icon: Headphones,
    prompt: 'Ik wil een medewerker spreken',
    example: 'KV-77830',
  },
]
type Message = {
  role: 'assistant' | 'user'
  text: string
  time: string
  order?: Order | null
  caseId?: number | null
}
const now = () =>
  new Intl.DateTimeFormat('nl-NL', { hour: '2-digit', minute: '2-digit' }).format(new Date())
const newSession = () => {
  const id = crypto.randomUUID().replaceAll('-', '')
  sessionStorage.setItem('demo-session-id', id)
  return id
}
const session = () => sessionStorage.getItem('demo-session-id') || newSession()

function OrderCard({ order }: { order: Order }) {
  return (
    <div className="order-card">
      <div className="order-card-head">
        <div>
          <small>VOORBEELDBESTELLING</small>
          <h4>{order.order_id}</h4>
        </div>
        <span className="pill">{order.status}</span>
      </div>
      <div className="order-facts">
        <div>
          <span>Bezorging</span>
          <strong>{order.delivery_status}</strong>
        </div>
        <div>
          <span>Retour in demo</span>
          <strong>
            {order.return_eligible === true
              ? 'Mogelijk'
              : order.return_eligible === false
                ? 'Beoordeling nodig'
                : 'Onzeker'}
          </strong>
        </div>
        <div>
          <span>Terugbetaling</span>
          <strong>{order.refund_status}</strong>
        </div>
      </div>
      <div className="order-items">
        {order.items.map((item) => (
          <div key={item.name}>
            <Box size={17} />
            <span>
              {item.name}
              <small>
                {item.condition} · {item.quantity_delivered}/{item.quantity_ordered} geleverd
              </small>
            </span>
          </div>
        ))}
      </div>
      {order.partner_order && (
        <p className="order-note">Partnerbestelling · afwijkende procedure mogelijk</p>
      )}
    </div>
  )
}

function Chat({ onTrace }: { onTrace: (trace: Trace[]) => void }) {
  const [mode, setMode] = useState<'demo' | 'rasa' | 'unknown'>('unknown')
  useEffect(() => {
    void api
      .status()
      .then((status) => setMode(status.mode))
      .catch(() => setMode('unknown'))
  }, [])
  const [sessionId, setSessionId] = useState(session)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      text: 'Hoi! Ik help je met fictieve voorbeeldbestellingen. Kies een onderwerp of stel je vraag.',
      time: now(),
    },
  ])
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const [quick, setQuick] = useState(['Bestelling volgen', 'Artikel ontbreekt', 'Retourneren'])
  const [active, setActive] = useState<Issue | undefined>()
  const body = useRef<HTMLDivElement>(null)
  useEffect(() => {
    body.current?.scrollTo({ top: body.current.scrollHeight, behavior: 'smooth' })
  }, [messages, pending])
  const send = async (message: string, category?: Issue) => {
    const text = message.trim()
    if (!text || pending) return
    setDraft('')
    setPending(true)
    setMessages((current) => [...current, { role: 'user', text, time: now() }])
    try {
      const reply: Reply = await api.chat(sessionId, text, category ?? active)
      setMessages((current) => [
        ...current,
        ...reply.messages.map((answer, index): Message => ({
          role: 'assistant',
          text: answer,
          time: now(),
          order: index === 0 ? reply.order : null,
          caseId: index === 0 ? reply.case_id : null,
        })),
      ])
      setQuick(reply.quick_replies)
      onTrace(reply.trace)
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          text: `Het gesprek kon niet worden verwerkt. ${error instanceof Error ? error.message : 'Probeer het opnieuw.'}`,
          time: now(),
        },
      ])
    } finally {
      setPending(false)
    }
  }
  const select = (category: (typeof categories)[number]) => {
    setActive(category.id)
    document.getElementById('chat')?.scrollIntoView({ behavior: 'smooth' })
    void send(category.prompt, category.id)
  }
  useEffect(() => {
    const handler = (event: Event) => {
      const id = (event as CustomEvent<Issue>).detail
      select(
        categories.find((c) => c.id === id) || {
          id: 'partner',
          title: 'Partnerbestelling',
          description: 'Partnerprocedure',
          icon: Package,
          prompt: 'Ik heb een vraag over een partnerbestelling',
          example: 'KV-77830',
        },
      )
    }
    window.addEventListener('support-category', handler)
    return () => window.removeEventListener('support-category', handler)
  }, [pending, active, sessionId])
  return (
    <section className="chat-shell" id="chat" aria-label="Voorbeeldgesprek">
      <div className="chat-top">
        <div className="avatar">
          <MessageCircle size={22} />
        </div>
        <div>
          <strong>Support assistent</strong>
          <span>
            <i className="online" />{' '}
            {mode === 'rasa' ? 'Rasa modus' : mode === 'demo' ? 'Demo modus' : 'Status onbekend'} ·{' '}
            {active
              ? categories.find((c) => c.id === active)?.title || 'Partnerbestelling'
              : 'Klaar om te helpen'}
          </span>
        </div>
        <button
          className="icon-button reset"
          title="Nieuw gesprek"
          aria-label="Nieuw gesprek"
          onClick={() => {
            setSessionId(newSession())
            setMessages([
              {
                role: 'assistant',
                text: 'Nieuw gesprek gestart. Waarmee kan ik je helpen?',
                time: now(),
              },
            ])
            setActive(undefined)
            setQuick(['Bestelling volgen', 'Artikel ontbreekt', 'Retourneren'])
            onTrace([])
          }}
        >
          <RotateCcw size={18} />
        </button>
      </div>
      <div className="chat-body" ref={body} aria-live="polite">
        <div className="chat-date">VANDAAG · VOORBEELDGESPREK</div>
        {messages.map((message, index) => (
          <div className={`message-row ${message.role}`} key={index}>
            {message.role === 'assistant' && (
              <div className="mini-avatar">
                <MessageCircle size={15} />
              </div>
            )}
            <div className="message-stack">
              <div className="bubble">{message.text}</div>
              {message.order && <OrderCard order={message.order} />}
              <small>{message.time}</small>
            </div>
          </div>
        ))}
        {pending && (
          <div className="message-row assistant">
            <div className="mini-avatar">
              <MessageCircle size={15} />
            </div>
            <div className="bubble processing">Gegevens verwerken…</div>
          </div>
        )}
      </div>
      <div className="chat-bottom">
        {quick.length > 0 && (
          <div className="quick-replies">
            {quick.map((label) => (
              <button key={label} onClick={() => send(label)} disabled={pending}>
                {label}
                <ArrowUpRight size={14} />
              </button>
            ))}
          </div>
        )}
        <form
          onSubmit={(event) => {
            event.preventDefault()
            void send(draft)
          }}
        >
          <label className="sr-only" htmlFor="chat-input">
            Typ je bericht
          </label>
          <input
            id="chat-input"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={
              active ? 'Typ je voorbeeldordernummer of vraag…' : 'Stel je vraag of typ KV-10482…'
            }
            disabled={pending}
          />
          <button aria-label="Verstuur bericht" disabled={!draft.trim() || pending}>
            <Send size={18} />
          </button>
        </form>
        <small>
          Fictieve data · Geen echte Kruidvat klantenservice · Gebruik geen echte persoonsgegevens
        </small>
      </div>
    </section>
  )
}

function Operations() {
  const [token, setToken] = useState(sessionStorage.getItem('ops-token') || '')
  const [publicDemo, setPublicDemo] = useState<boolean | null>(null)
  const [cases, setCases] = useState<Case[]>([])
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<number | null>(null)
  const load = async (value = publicDemo ? session() : token, demo = publicDemo === true) => {
    try {
      const rows = await api.cases(value, demo)
      setCases(rows)
      setError('')
      if (!demo) sessionStorage.setItem('ops-token', value)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Cases niet beschikbaar.')
    }
  }
  useEffect(() => {
    void api
      .status()
      .then((status) => {
        if (status.deployment === 'cloudflare') {
          setPublicDemo(true)
          void load(session(), true)
        } else {
          setPublicDemo(false)
          if (token) void load(token, false)
        }
      })
      .catch(() => {
        setPublicDemo(false)
        setError('De dienst is niet beschikbaar.')
      })
  }, [])
  const update = async (id: number, body: { status?: Case['status']; assignee?: string }) => {
    try {
      await api.updateCase(id, publicDemo ? session() : token, body, publicDemo === true)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Bijwerken mislukt.')
    }
  }
  const filtered = cases.filter(
    (c) =>
      (filter === 'all' || c.status === filter) &&
      `${c.id} ${c.order_id} ${c.issue} ${c.summary}`.toLowerCase().includes(query.toLowerCase()),
  )
  const current = cases.find((c) => c.id === selected)
  return (
    <main className="workspace">
      <div className="section-intro">
        <span className="eyebrow">SUPPORT OPERATIONS / SIMULATIE</span>
        <h1>
          Elke overdracht,
          <br />
          <em>met de juiste context.</em>
        </h1>
        <p>
          Een medewerker ziet waarom een gesprek is doorgestuurd, welke voorbeeldorder erbij hoort
          en wat de volgende stap is.
        </p>
      </div>
      <div className="ops-login">
        <ShieldCheck size={19} />
        {publicDemo ? (
          <span>
            Je ziet alleen de fictieve cases uit deze browsersessie. Er vindt geen echte overdracht
            plaats.
          </span>
        ) : publicDemo === null ? (
          <span>Werkruimte laden…</span>
        ) : (
          <>
            <span>
              Deze werkruimte vereist een lokale toegangscode. Cases bevatten uitsluitend fictieve
              gegevens.
            </span>
            <input
              aria-label="Operations toegangscode"
              type="password"
              value={token}
              placeholder="Toegangscode"
              onChange={(e) => setToken(e.target.value)}
            />
            <button className="button primary" onClick={() => void load()} disabled={!token}>
              Open werkruimte
            </button>
          </>
        )}
      </div>
      {error && (
        <div className="alert" role="alert">
          {error}
        </div>
      )}
      <div className="ops-stats">
        <div>
          <span>Open cases</span>
          <strong>{cases.filter((c) => c.status === 'open').length}</strong>
        </div>
        <div>
          <span>In onderzoek</span>
          <strong>{cases.filter((c) => c.status === 'investigating').length}</strong>
        </div>
        <div>
          <span>Afgerond</span>
          <strong>{cases.filter((c) => c.status === 'resolved').length}</strong>
        </div>
      </div>
      <div className="ops-layout">
        <section className="panel">
          <div className="panel-title">
            <h2>Caseoverzicht</h2>
            <button className="text-button" onClick={() => void load()}>
              Vernieuwen <RotateCcw size={15} />
            </button>
          </div>
          <div className="filters">
            <div className="search">
              <Search size={17} />
              <input
                aria-label="Zoek cases"
                placeholder="Zoek op case of order…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <select
              aria-label="Filter status"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">Alle statussen</option>
              <option value="open">Open</option>
              <option value="investigating">In onderzoek</option>
              <option value="resolved">Afgerond</option>
            </select>
          </div>
          <div className="case-list">
            {filtered.map((c) => (
              <button
                className={`case-row ${selected === c.id ? 'selected' : ''}`}
                onClick={() => setSelected(c.id)}
                key={c.id}
              >
                <span className="case-icon">
                  <Headphones size={19} />
                </span>
                <span>
                  <strong>
                    Case #{c.id} · {c.issue}
                  </strong>
                  <small>
                    {c.order_id || 'Geen order'} · {c.created_at}
                  </small>
                </span>
                <span className={`status ${c.status}`}>
                  {c.status === 'investigating'
                    ? 'In onderzoek'
                    : c.status === 'resolved'
                      ? 'Afgerond'
                      : 'Open'}
                </span>
              </button>
            ))}
            {filtered.length === 0 && (
              <p className="empty">
                Nog geen cases zichtbaar. Probeer in de klantendemo een beschadigd artikel of een
                ontbrekend artikel.
              </p>
            )}
          </div>
        </section>
        <aside className="panel case-detail">
          {current ? (
            <>
              <span className="eyebrow">CASE #{current.id}</span>
              <h2>{current.reason}</h2>
              <p>{current.summary}</p>
              <dl>
                <div>
                  <dt>Voorbeeldorder</dt>
                  <dd>{current.order_id || 'Niet gekoppeld'}</dd>
                </div>
                <div>
                  <dt>Onderwerp</dt>
                  <dd>{current.issue}</dd>
                </div>
                <div>
                  <dt>Toegewezen aan</dt>
                  <dd>{current.assignee || 'Nog niemand'}</dd>
                </div>
              </dl>
              <label>
                Status{' '}
                <select
                  value={current.status}
                  onChange={(e) =>
                    void update(current.id, { status: e.target.value as Case['status'] })
                  }
                >
                  <option value="open">Open</option>
                  <option value="investigating">In onderzoek</option>
                  <option value="resolved">Afgerond</option>
                </select>
              </label>
              <label>
                Medewerker{' '}
                <input
                  value={current.assignee || ''}
                  placeholder="Naam medewerker"
                  onChange={(e) =>
                    setCases((rows) =>
                      rows.map((row) =>
                        row.id === current.id ? { ...row, assignee: e.target.value } : row,
                      ),
                    )
                  }
                  onBlur={(e) => void update(current.id, { assignee: e.target.value })}
                />
              </label>
              <p className="hint">Toewijzing is een simulatie; er wordt niemand extern benaderd.</p>
            </>
          ) : (
            <div className="detail-placeholder">
              <CircleHelp size={34} />
              <h3>Selecteer een case</h3>
              <p>Open een case om ordercontext en vervolgstappen te bekijken.</p>
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}

function Explorer({ trace }: { trace: Trace[] }) {
  const [status, setStatus] = useState<Status | null>(null)
  useEffect(() => {
    void api
      .status()
      .then(setStatus)
      .catch(() => setStatus(null))
  }, [])
  const services = [
    ['Browser', 'React interface en getypeerde API-client'],
    ['API-laag', 'FastAPI valideert verzoeken en kiest de adapter'],
    ['Gesprek', 'Rasa REST in licentiemodus of deterministische demo'],
    ['Acties & beleid', 'Rasa SDK actie / gedeelde demo-regels'],
    ['Retail API & SQLite', 'Fictieve orders, sessies en cases'],
  ]
  return (
    <main className="explorer">
      <div className="section-intro">
        <span className="eyebrow">ARCHITECTUUR & SYSTEEMEXPLORER</span>
        <h1>
          Van klantvraag
          <br />
          <em>naar onderbouwde actie.</em>
        </h1>
        <p>
          Volg de gegevens van de browser tot de order en de case. Deze weergave toont de
          daadwerkelijk geconfigureerde modus.
        </p>
      </div>
      <div className="explorer-grid">
        <section className="panel architecture">
          <div className="panel-title">
            <h2>Servicepad</h2>
            <span className="badge">{status?.mode === 'rasa' ? 'Rasa modus' : 'Demo modus'}</span>
          </div>
          <div className="architecture-path">
            {services.map(([name, description], index) => (
              <div className="architecture-step" key={name}>
                <span className="step-number">0{index + 1}</span>
                <div>
                  <strong>{name}</strong>
                  <p>{description}</p>
                </div>
                {index < services.length - 1 && <ArrowRight size={19} />}
              </div>
            ))}
          </div>
        </section>
        <section className="panel live-status">
          <div className="panel-title">
            <h2>Live servicestatus</h2>
            <button
              className="text-button"
              onClick={() =>
                void api
                  .status()
                  .then(setStatus)
                  .catch(() => setStatus(null))
              }
            >
              Vernieuwen <RotateCcw size={15} />
            </button>
          </div>
          {[
            ['Retail API', status?.retail_api],
            ['Caseopslag', status?.case_store],
            ['Rasa server', status?.rasa],
          ].map(([name, value]) => (
            <div className="service-row" key={name}>
              <span>{name}</span>
              <strong className={value === 'ok' ? 'healthy' : 'muted'}>
                <i className={value === 'ok' ? 'online' : 'offline'} />
                {value === 'ok'
                  ? 'Beschikbaar'
                  : value === 'not_configured'
                    ? 'Niet geconfigureerd'
                    : 'Niet bereikbaar'}
              </strong>
            </div>
          ))}
          <p className="hint">
            Deze status komt van de API. Een Rasa status zegt niets over verborgen actie-uitvoering.
          </p>
        </section>
        <section className="panel trace-panel">
          <div className="panel-title">
            <h2>Laatste gespreksstappen</h2>
            <span className="badge">
              {status?.mode === 'rasa' ? 'REST-observatie' : 'Gesimuleerd pad'}
            </span>
          </div>
          {trace.length ? (
            trace.map((item, index) => (
              <div className="trace-row" key={index}>
                <span>{index + 1}</span>
                <div>
                  <strong>{item.step}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))
          ) : (
            <p className="empty">Start een gesprek om een trace te zien.</p>
          )}
        </section>
        <section className="panel concepts">
          <h2>Waarom deze opbouw?</h2>
          <p>
            <strong>Rasa</strong> beheert in de gelicentieerde modus het gesprek, slots en acties.
            De REST-adapter geeft tekst terug aan de browser.
          </p>
          <p>
            <strong>FastAPI</strong> valideert de browsercontracten, levert fictieve orders en
            bewaart cases in SQLite.
          </p>
          <p>
            <strong>Deterministische regels</strong> bepalen of een demo-order hulp van een
            medewerker nodig heeft. Er worden geen echte betalingen of retouren verwerkt.
          </p>
          <p>
            <strong>Docker Compose</strong> verbindt draaiende containers. Een image is het
            bouwpakket; een container is het actieve proces. CI bouwt en test code vóór publicatie.
          </p>
        </section>
      </div>
    </main>
  )
}

function CaseStudy() {
  return (
    <main className="case-study">
      <div className="section-intro">
        <span className="eyebrow">DE BUSINESSCASE</span>
        <h1>
          Een servicegesprek
          <br />
          <em>dat ergens toe leidt.</em>
        </h1>
        <p>
          Een concept voor ordergerichte selfservice: sneller relevante context verzamelen en
          complexe uitzonderingen duidelijk overdragen.
        </p>
      </div>
      <div className="study-grid">
        {[
          [
            '01 / DE UITDAGING',
            'Een FAQ kent je bestelling niet',
            'Veel klantvragen lijken eenvoudig, maar vergen inzicht in leveringen, artikelen of terugbetalingen.',
          ],
          [
            '02 / DE AANPAK',
            'Van vraag naar ordercontext',
            'Het gesprek verzamelt een ordernummer, leest gestructureerde data en past expliciete voorbeeldregels toe.',
          ],
          [
            '03 / DE OVERDRACHT',
            'Menselijke beoordeling waar nodig',
            'Schade, ontbrekende artikelen en partneruitzonderingen leveren een case met reden en samenvatting op.',
          ],
          [
            '04 / DE GRENZEN',
            'Een bewijsbaar prototype',
            'Orders en cases zijn fictief. Er is geen live retailerintegratie of aangetoonde besparing. Een pilot vereist toestemming, privacyontwerp, authenticatie en operationele meting.',
          ],
        ].map(([label, title, body]) => (
          <article key={label}>
            <span className="eyebrow">{label}</span>
            <h2>{title}</h2>
            <p>{body}</p>
          </article>
        ))}
      </div>
      <div className="study-callout">
        <Sparkles size={25} />
        <div>
          <h2>Van prototype naar pilot</h2>
          <p>
            Valideer eerst klantproblemen met een retailer. Koppel daarna een beveiligde orderbron,
            meet taakafronding en escalatiekwaliteit, toets retourbeleid juridisch en betrek
            servicemedewerkers bij evaluatie.
          </p>
        </div>
      </div>
    </main>
  )
}

export function App() {
  const [page, setPage] = useState<'home' | 'operations' | 'explorer' | 'study'>('home')
  const [menu, setMenu] = useState(false)
  const [trace, setTrace] = useState<Trace[]>([])
  const go = (target: typeof page) => {
    setPage(target)
    setMenu(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const openCategory = (id: Issue) => {
    go('home')
    setTimeout(() => window.dispatchEvent(new CustomEvent('support-category', { detail: id })), 50)
  }
  return (
    <>
      <div className="demo-banner">
        <span className="demo-dot" /> ONAFHANKELIJKE PORTFOLIODEMO{' '}
        <span className="banner-divider">/</span> FICTIEVE BESTELLINGEN <ArrowUpRight size={13} />
      </div>
      <header className="site-header">
        <div className="header-inner">
          <button className="brand" onClick={() => go('home')} aria-label="Naar startpagina">
            <span className="brand-mark">
              K<span>·</span>
            </span>
            <span>
              support<span className="brand-sub">RETAIL SERVICE LAB</span>
            </span>
          </button>
          <nav className={menu ? 'open' : ''} aria-label="Hoofdnavigatie">
            <button className={page === 'home' ? 'active' : ''} onClick={() => go('home')}>
              Klantenservice
            </button>
            <button
              className={page === 'operations' ? 'active' : ''}
              onClick={() => go('operations')}
            >
              Support Operations
            </button>
            <button className={page === 'explorer' ? 'active' : ''} onClick={() => go('explorer')}>
              Architectuur
            </button>
            <button className={page === 'study' ? 'active' : ''} onClick={() => go('study')}>
              De businesscase
            </button>
          </nav>
          <button
            className="header-cta"
            onClick={() =>
              page === 'home'
                ? document.getElementById('chat')?.scrollIntoView({ behavior: 'smooth' })
                : go('home')
            }
          >
            Start de demo <ArrowUpRight size={17} />
          </button>
          <button
            className="menu-button"
            aria-label={menu ? 'Sluit menu' : 'Open menu'}
            onClick={() => setMenu(!menu)}
          >
            {menu ? <X /> : <Menu />}
          </button>
        </div>
      </header>
      {page === 'home' ? (
        <>
          <main>
            <section className="hero">
              <div className="hero-inner">
                <div className="hero-copy">
                  <div className="prototype-badge">
                    <Workflow size={16} aria-hidden="true" />
                    <strong>Rasa prototype</strong>
                    <span aria-hidden="true">·</span>
                    <span>Live demo uses deterministic rules</span>
                  </div>
                  <span className="eyebrow">
                    <span className="tiny-line" /> SLIMME HULP VOOR ELKE BESTELLING
                  </span>
                  <h1>
                    Waar kunnen we je
                    <br />
                    vandaag <em>mee helpen?</em>
                  </h1>
                  <p>
                    Van je bestelling volgen tot een beschadigd artikel: ontdek hoe goede
                    klantenservice begint met de juiste informatie.
                  </p>
                  <div className="hero-actions">
                    <button
                      className="button primary"
                      onClick={() =>
                        document.getElementById('chat')?.scrollIntoView({ behavior: 'smooth' })
                      }
                    >
                      Stel je vraag <ArrowRight size={18} />
                    </button>
                    <button
                      className="button secondary"
                      onClick={() =>
                        document
                          .getElementById('categories')
                          ?.scrollIntoView({ behavior: 'smooth' })
                      }
                    >
                      Bekijk onderwerpen <ChevronDown size={18} />
                    </button>
                  </div>
                  <div className="hero-proof">
                    <span>
                      <Check size={16} /> Direct een voorbeeld proberen
                    </span>
                    <span>
                      <Check size={16} /> Geen account nodig
                    </span>
                  </div>
                </div>
                <div className="hero-visual">
                  <div className="hero-orbit orbit-one" />
                  <div className="hero-orbit orbit-two" />
                  <div className="floating-card top">
                    <span className="floating-icon yellow">
                      <PackageCheck size={20} />
                    </span>
                    <div>
                      <small>BESTELLING GEVONDEN</small>
                      <strong>KV-10482</strong>
                    </div>
                    <span className="floating-check">
                      <Check size={16} />
                    </span>
                  </div>
                  <div className="assistant-art">
                    <span className="art-bubble a" />
                    <span className="art-bubble b" />
                    <div className="face">
                      <span className="eye" />
                      <span className="eye" />
                      <span className="smile" />
                    </div>
                    <span className="art-spark one">✦</span>
                    <span className="art-spark two">✳</span>
                  </div>
                  <div className="floating-card bottom">
                    <span className="floating-icon red">
                      <Headphones size={20} />
                    </span>
                    <div>
                      <small>WANNEER HET NODIG IS</small>
                      <strong>Persoonlijke opvolging</strong>
                    </div>
                  </div>
                </div>
              </div>
            </section>
            <section className="trust-strip">
              <div>
                <span>
                  <Clock3 size={20} />
                </span>
                <strong>Een duidelijk antwoord</strong>
                <small>Gebaseerd op voorbeeldorderdata</small>
              </div>
              <div>
                <span>
                  <ShieldCheck size={20} />
                </span>
                <strong>Heldere vervolgstappen</strong>
                <small>Met grenzen en uitzonderingen</small>
              </div>
              <div>
                <span>
                  <Headphones size={20} />
                </span>
                <strong>Menselijke hulp</strong>
                <small>Met de context al verzameld</small>
              </div>
            </section>
            <section className="categories section-wrap" id="categories">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">WAARMEE KUNNEN WE HELPEN?</span>
                  <h2>
                    Wat speelt er met
                    <br />
                    <em>jouw bestelling?</em>
                  </h2>
                </div>
                <p>Kies een onderwerp. De assistent start meteen een gericht voorbeeldgesprek.</p>
              </div>
              <div className="category-grid">
                {categories.map((c) => (
                  <button className="category-card" key={c.id} onClick={() => openCategory(c.id)}>
                    <span className="category-icon">
                      <c.icon size={27} strokeWidth={1.8} />
                    </span>
                    <span className="category-text">
                      <strong>{c.title}</strong>
                      <small>{c.description}</small>
                    </span>
                    <ArrowUpRight size={19} className="category-arrow" />
                  </button>
                ))}
              </div>
            </section>
            <section className="demo-section">
              <div className="section-wrap demo-grid">
                <div className="demo-copy">
                  <span className="eyebrow">PROBEER HET ZELF</span>
                  <h2>
                    Een goed gesprek
                    <br />
                    begint <em>hier.</em>
                  </h2>
                  <p>
                    Open een voorbeeldgesprek en zie hoe een vraag verandert in heldere
                    orderinformatie en, wanneer nodig, een case voor opvolging.
                  </p>
                  <div className="sample-panel">
                    <strong>Probeer deze voorbeeldorders</strong>
                    {[
                      ['KV-10482', 'Ontbrekend artikel', 'missing'],
                      ['KV-20991', 'Beschadigd artikel', 'damaged'],
                      ['KV-77830', 'Partnerbestelling', 'partner'],
                    ].map(([id, label, issue]) => (
                      <button key={id} onClick={() => openCategory(issue as Issue)}>
                        <span>{id}</span>
                        <small>{label}</small>
                        <ArrowUpRight size={17} />
                      </button>
                    ))}
                  </div>
                  <p className="demo-disclaimer">
                    <ShieldCheck size={17} /> Onafhankelijke demonstratie, niet verbonden aan
                    Kruidvat. Alle klant- en ordergegevens zijn fictief.
                  </p>
                </div>
                <Chat onTrace={setTrace} />
              </div>
            </section>
            <section className="closing-cta section-wrap">
              <div>
                <span className="eyebrow">ACHTER DE SCHERMEN</span>
                <h2>Meer dan een chatbot.</h2>
                <p>
                  Bekijk hoe het gesprek, de orderdata en de menselijke overdracht technisch
                  samenkomen.
                </p>
              </div>
              <button className="button light" onClick={() => go('explorer')}>
                Ontdek de architectuur <ArrowRight size={18} />
              </button>
            </section>
          </main>
        </>
      ) : page === 'operations' ? (
        <Operations />
      ) : page === 'explorer' ? (
        <Explorer trace={trace} />
      ) : (
        <CaseStudy />
      )}
      <footer>
        <div className="footer-inner">
          <div>
            <strong className="footer-brand">K· support</strong>
            <p>
              Een onafhankelijk engineeringportfolio van Nicholai Gay.
              <br />
              Fictieve retaildata. Geen officiële Kruidvat dienst.
            </p>
          </div>
          <div>
            <button onClick={() => go('home')}>Klantenservice</button>
            <button onClick={() => go('operations')}>Operations</button>
            <button onClick={() => go('explorer')}>Architectuur</button>
            <button onClick={() => go('study')}>Businesscase</button>
          </div>
          <a href="https://profile.nickcloud.dev/" target="_blank" rel="noreferrer">
            Bekijk portfolio <ArrowUpRight size={16} />
          </a>
        </div>
      </footer>
    </>
  )
}
