import React, { useState, useEffect } from 'react';
import { useUser, useAuth, SignIn, UserButton } from '@clerk/clerk-react';
import './index.css';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ASSETS = [
    { id: 'XAUUSD', name: 'GOLD', category: 'Commodities' },
    { id: 'EURUSD', name: 'EUR/USD', category: 'Forex' },
    { id: 'BTCUSD', name: 'BITCOIN', category: 'Crypto' },
    { id: 'GBPUSD', name: 'GBP/USD', category: 'Forex' },
];

type Tab = 'analysis' | 'subscription' | 'affiliates';

export default function App() {
    const { isSignedIn, isLoaded: userLoaded, user } = useUser();
    const { getToken } = useAuth();

    const [activeTab, setActiveTab] = useState<Tab>('analysis');
    const [showConsent, setShowConsent] = useState<boolean>(false);
    const [analyzing, setAnalyzing] = useState<boolean>(false);
    const [selectedAsset, setSelectedAsset] = useState<string>('XAUUSD');
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [paymentSent, setPaymentSent] = useState<boolean>(false);
    const [txRef, setTxRef] = useState<string>('');

    // Affiliate Data
    const [isAffiliate, setIsAffiliate] = useState<boolean>(false);
    const [affloading, setAffLoading] = useState<boolean>(false);
    const [affStats, setAffStats] = useState<any>(null);

    // Check consent on mount (localStorage)
    useEffect(() => {
        if (isSignedIn && user) {
            const consentKey = `softi_consent_${user.id}`;
            if (!localStorage.getItem(consentKey)) {
                setShowConsent(true);
            }
        }
    }, [isSignedIn, user]);

    // Helper function to make authenticated API calls
    const authFetch = async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        return fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`,
            },
        });
    };

    useEffect(() => {
        if (isSignedIn && activeTab === 'affiliates') {
            fetchAffiliateData();
        }
    }, [isSignedIn, activeTab]);

    const fetchAffiliateData = () => {
        setAffLoading(true);
        authFetch(`${API_BASE}/affiliates/dashboard`)
            .then(r => {
                if (r.status === 404) {
                    setIsAffiliate(false);
                    return null;
                }
                return r.json();
            })
            .then(data => {
                if (data && data.status === 'success') {
                    setAffStats(data.data);
                    setIsAffiliate(true);
                }
                setAffLoading(false);
            })
            .catch(() => setAffLoading(false));
    };

    const joinAffiliateProgram = () => {
        setAffLoading(true);
        authFetch(`${API_BASE}/affiliates/join`, { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    fetchAffiliateData();
                } else {
                    setAffLoading(false);
                }
            })
            .catch(() => setAffLoading(false));
    };

    const handleAcceptConsent = () => {
        if (user) {
            const consentKey = `softi_consent_${user.id}`;
            localStorage.setItem(consentKey, 'accepted');
        }
        setShowConsent(false);

        // Also try to save to backend (fire-and-forget)
        authFetch(`${API_BASE}/consent/acknowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ version: "1.0" })
        }).catch(() => { }); // Silently fail if backend is unreachable
    };

    const runAnalysis = () => {
        setAnalyzing(true);
        setAnalysisResult(null);
        authFetch(`${API_BASE}/analyze?symbol=${selectedAsset}`)
            .then(r => r.json())
            .then(data => {
                setAnalysisResult(data);
                setAnalyzing(false);
            })
            .catch(() => setAnalyzing(false));
    };

    const submitPayment = (method: string) => {
        if (!txRef) return alert("Inserisci il riferimento della transazione");

        authFetch(`${API_BASE}/payments/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount: 29.00,
                currency: 'EUR',
                method: method,
                tx_reference: txRef
            })
        })
            .then(r => r.json())
            .then(() => {
                setPaymentSent(true);
                setTxRef('');
            });
    };

    const copyLink = () => {
        const link = `https://softianalyze.it/ref/${affStats.ref_code}`;
        navigator.clipboard.writeText(link);
        alert("Link copiato negli appunti!");
    };

    const getBiasClass = (bias: string) => {
        if (bias?.includes('BULLISH')) return 'bias-bullish';
        if (bias?.includes('BEARISH')) return 'bias-bearish';
        return 'bias-neutral';
    };

    // --- RENDER STATES ---

    // 1. Still loading Clerk
    if (!userLoaded) return null;

    // 2. Not signed in → show Clerk login
    if (!isSignedIn) {
        return (
            <div className="app-shell">
                <header className="nav-lite">
                    <div className="logo">SOFTI<span>ANALYZE</span></div>
                </header>
                <div className="consent-wrapper">
                    <SignIn routing="hash" />
                </div>
            </div>
        );
    }

    // 3. Signed in → show dashboard (with consent popup overlay if needed)
    return (
        <div className="app-shell">
            <header className="nav-lite">
                <div className="logo">SOFTI<span>ANALYZE</span></div>
                <div className="nav-right">
                    <div className="nav-plan-info">
                        Plan: <span className="nav-plan-tag">LITE</span>
                    </div>
                    <UserButton afterSignOutUrl="/" />
                </div>
            </header>

            {/* === CONSENT POPUP OVERLAY === */}
            {showConsent && (
                <div className="consent-overlay" onClick={(e) => e.stopPropagation()}>
                    <div className="consent-popup glass-panel">
                        <div className="consent-popup-icon">⚖️</div>
                        <h2>Avviso Legale</h2>
                        <div className="consent-text">
                            <p>Benvenuto in Softi Analyze. Proseguendo, dichiari di aver compreso che questa piattaforma fornisce esclusivamente <strong>analisi tecniche deterministiche</strong> a scopo educativo.</p>
                            <br />
                            <p>Non siamo consulenti finanziari. Nessun dato mostrato deve essere interpretato come un segnale di acquisto o vendita. Il trading comporta rischi elevati per il tuo capitale.</p>
                        </div>
                        <button className="btn-premium" onClick={handleAcceptConsent}>ACCETTO E PROSEGUO</button>
                    </div>
                </div>
            )}

            <div className="container fade-in-up">
                <nav className="nav-tabs">
                    <div className={`nav-tab ${activeTab === 'analysis' ? 'active' : ''}`} onClick={() => setActiveTab('analysis')}>Analisi</div>
                    <div className={`nav-tab ${activeTab === 'subscription' ? 'active' : ''}`} onClick={() => setActiveTab('subscription')}>Abbonamento</div>
                    <div className={`nav-tab ${activeTab === 'affiliates' ? 'active' : ''}`} onClick={() => setActiveTab('affiliates')}>Affiliati</div>
                </nav>

                {activeTab === 'analysis' && (
                    <div className="view-analysis">
                        <div className="view-header">
                            <h1 className="view-title">Market Analysis</h1>
                            <p className="text-dim">Seleziona l'asset e avvia il calcolo deterministico.</p>
                        </div>
                        <div className="selection-grid">
                            {ASSETS.map(asset => (
                                <div key={asset.id} className={`glass-panel asset-card ${selectedAsset === asset.id ? 'active' : ''}`} onClick={() => setSelectedAsset(asset.id)}>
                                    <div className="asset-category">{asset.category}</div>
                                    <div className="asset-name">{asset.name}</div>
                                </div>
                            ))}
                        </div>
                        <div className="analysis-controls">
                            {!analyzing ? (
                                <button className="btn-premium btn-analysis-large" onClick={runAnalysis}>AVVIA ANALISI {selectedAsset}</button>
                            ) : (
                                <div className="loader-container"><div className="loader"></div><div className="loading-text">ELABORAZIONE DATI DETERMINISTICI...</div></div>
                            )}
                        </div>
                        {analysisResult && !analyzing && (
                            <div className="result-section">
                                <div className="glass-panel result-container">
                                    <div className="result-header">
                                        <div><h2 className="result-symbol">{analysisResult.symbol}</h2><p className="text-dim">Status: Deterministic Render Complete</p></div>
                                        <div className={`bias-indicator ${getBiasClass(analysisResult.bias)}`}>{analysisResult.bias}</div>
                                    </div>
                                    <div className="results-grid">
                                        <div className="res-card glass-panel res-card-bg">
                                            <h3>Market Regime</h3>
                                            <div className="regime-value">{analysisResult.regime || 'STABLE'}</div>
                                            <p className="regime-desc">Fase di {analysisResult.regime?.toLowerCase()}. Probabile continuazione.</p>
                                        </div>
                                        <div className="res-card glass-panel res-card-bg">
                                            <h3>Key Levels</h3>
                                            <ul className="levels-list">{analysisResult.key_levels?.map((lvl: any, i: number) => (<li key={i} className="level-item"><span>{lvl.label}</span><span className="level-val">{lvl.price}</span></li>))}</ul>
                                        </div>
                                    </div>
                                    {analysisResult.pro_data || analysisResult.narrative ? (
                                        <div className="pro-card fade-in-up">
                                            <div className="pro-header">
                                                <span className="pro-icon">✦</span>
                                                <h2 className="pro-title">PRO Analysis Insights</h2>
                                            </div>
                                            {analysisResult.narrative && (
                                                <div className="section-narrative">
                                                    <h3 className="narrative-header">AI Market Narrative</h3>
                                                    <div className="ai-narrative-text">{analysisResult.narrative}</div>
                                                </div>
                                            )}
                                            {analysisResult.pro_data && (
                                                <div className="results-grid pro-data-grid">
                                                    <div>
                                                        <h3 className="pro-section-title">Order Blocks Detected</h3>
                                                        {analysisResult.pro_data.order_blocks && analysisResult.pro_data.order_blocks.length > 0 ? (
                                                            <div className="ob-list">
                                                                {analysisResult.pro_data.order_blocks.map((ob: any, i: number) => (
                                                                    <div key={i} className={`ob-item ob-${ob.type.toLowerCase()}`}>
                                                                        <div><span className="ob-label">{ob.type} OB</span><span className="ob-tf">{ob.timeframe}</span></div>
                                                                        <div className="ob-price">{ob.price_range[0]} - {ob.price_range[1]}</div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : (<p className="empty-msg">No specific order blocks detected currently.</p>)}
                                                    </div>
                                                    <div>
                                                        <h3 className="pro-section-title">Fair Value Gaps (FVG)</h3>
                                                        {analysisResult.pro_data.fair_value_gaps && analysisResult.pro_data.fair_value_gaps.length > 0 ? (
                                                            <div className="ob-list">
                                                                {analysisResult.pro_data.fair_value_gaps.map((fvg: any, i: number) => (
                                                                    <div key={i} className="fvg-item">
                                                                        <span>Gap Zone ({fvg.timeframe})</span>
                                                                        <span>{fvg.price_range[0]} - {fvg.price_range[1]}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : (<p className="empty-msg">Market is balanced, no notable FVGs found.</p>)}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="pro-teaser glass-panel" onClick={() => setActiveTab('subscription')}>
                                            <h2>🚀 Sblocca PRO</h2><p>Narrativa AI, Order Blocks e FVG.</p><button className="btn-premium">SCOPRI ORA</button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'subscription' && (
                    <div className="view-subscription">
                        <h1>Piani</h1><p className="text-dim">Scegli il tuo livello di precisione.</p>
                        <div className="pricing-grid">
                            <div className="glass-panel price-card">
                                <h2>LITE</h2><div className="price-value">FREE</div><div className="price-period">Per sempre</div>
                                <ul className="feature-list"><li className="feature-item"><span>✓</span> Bias Direzionale</li><li className="feature-item"><span>✓</span> Market Regime</li></ul>
                                <button className="btn-premium btn-lite-active">ATTIVO</button>
                            </div>
                            <div className="glass-panel price-card featured">
                                <div className="badge-popular">POPULAR</div>
                                <h2>PRO</h2><div className="price-value">€29</div><div className="price-period">Al mese</div>
                                <ul className="feature-list"><li className="feature-item"><span>✓</span> AI Market Narrative</li><li className="feature-item"><span>✓</span> Order Blocks & FVG</li></ul>
                                <button className="btn-premium">SBLOCCA PRO</button>
                            </div>
                        </div>
                        <div className="glass-panel payment-form">
                            <h3>Attivazione PRO</h3>
                            {paymentSent ? (
                                <div className="payment-success-msg"><h2 className="payment-success-title">Inviata!</h2><p className="text-dim">Verifica in corso.</p></div>
                            ) : (
                                <>
                                    <div className="iban-box">IT88 X 01234 12345 000000123456<br />USDT (TRC20): TX_ADDRESS_MOCK</div>
                                    <div className="form-group">
                                        <label htmlFor="tx-ref">TX Reference</label>
                                        <input id="tx-ref" type="text" className="form-input" placeholder="Inserisci l'ID della transazione" value={txRef} onChange={(e) => setTxRef(e.target.value)} />
                                    </div>
                                    <button className="btn-premium btn-full" onClick={() => submitPayment('Manual')}>CONFERMA</button>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'affiliates' && (
                    <div className="view-affiliates">
                        <h1>Affiliate Portal</h1>
                        <p className="text-dim">Guadagna commissioni ricorrenti promuovendo le analisi deterministiche.</p>
                        {affloading ? (
                            <div className="loader-container aff-loader"><div className="loader"></div><div className="loading-text">CARICAMENTO DATI AFFILIATO...</div></div>
                        ) : !isAffiliate ? (
                            <div className="glass-panel aff-join-card">
                                <h2 className="aff-join-title">Diventa un Partner</h2>
                                <p className="text-dim aff-join-desc">Unisciti al nostro programma e ottieni il <strong>30% di commissione</strong> su ogni utente PRO che porti in Softi Analyze. Pagamenti mensili automatici.</p>
                                <button className="btn-premium btn-join" onClick={joinAffiliateProgram}>ATTIVA ACCOUNT AFFILIATO</button>
                            </div>
                        ) : affStats && (
                            <>
                                <div className="affiliate-stats">
                                    <div className="glass-panel aff-stat-card"><div className="aff-stat-label">Referrals</div><div className="aff-stat-value">{affStats.total_referrals}</div></div>
                                    <div className="glass-panel aff-stat-card"><div className="aff-stat-label">Commissions Earned</div><div className="aff-stat-value">€{affStats.total_earned.toFixed(2)}</div></div>
                                    <div className="glass-panel aff-stat-card"><div className="aff-stat-label">Pending Payout</div><div className="aff-stat-value stat-pending">€{affStats.total_pending.toFixed(2)}</div></div>
                                </div>
                                <div className="glass-panel aff-link-box">
                                    <h3 className="box-title">Il tuo Affiliate Link</h3>
                                    <p className="text-dim box-desc">Condividi questo link per ottenere il 30% di commissione su ogni abbonamento PRO.</p>
                                    <div className="aff-link-container">
                                        <input id="aff-link-input" type="text" className="aff-link-input" readOnly value={`https://softianalyze.it/ref/${affStats.ref_code}`} aria-label="Your affiliate link" placeholder="Affiliate Link" />
                                        <button className="btn-premium btn-copy" onClick={copyLink}>COPIA</button>
                                    </div>
                                </div>
                                <div className="glass-panel referrals-container">
                                    <h3 className="referrals-title">Referral Recenti</h3>
                                    <p className="text-dim referrals-empty">I dettagli dei singoli referral saranno disponibili a breve.</p>
                                </div>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
