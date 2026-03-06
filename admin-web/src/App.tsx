import React, { useState, useEffect } from 'react';
import './index.css';
import {
    LayoutDashboard,
    Users as UsersIcon,
    CreditCard,
    ShieldCheck,
    CheckCircle,
    User,
    Search,
    Inbox,
    ArrowUpCircle,
    ArrowDownCircle
} from 'lucide-react';
import { SignedIn, SignedOut, RedirectToSignIn, UserButton, useAuth } from '@clerk/clerk-react';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

type View = 'dashboard' | 'users' | 'payments';

function AdminPanel() {
    const { getToken } = useAuth();

    const [view, setView] = useState<View>('dashboard');
    const [stats, setStats] = useState<any>({});
    const [users, setUsers] = useState<any[]>([]);
    const [payments, setPayments] = useState<any[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [promoting, setPromoting] = useState<string | null>(null);

    // Helper function to make authenticated API calls
    const authFetch = async (url: string, options: RequestInit = {}) => {
        const token = await getToken();
        return fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });
    };

    useEffect(() => {
        fetchStats();
        fetchUsers();
        fetchPayments();
    }, []);

    const fetchStats = () => authFetch(`${API_BASE}/admin/stats`).then(r => r.json()).then(setStats).catch(() => { });
    const fetchUsers = () => authFetch(`${API_BASE}/admin/users`).then(r => r.json()).then(data => {
        if (Array.isArray(data)) setUsers(data);
    }).catch(() => { });
    const fetchPayments = () => authFetch(`${API_BASE}/admin/payments/pending`).then(r => r.json()).then(data => {
        if (Array.isArray(data)) setPayments(data);
    }).catch(() => { });

    const verifyPayment = (id: string) => {
        authFetch(`${API_BASE}/payments/${id}/verify`, { method: 'POST' })
            .then(() => { fetchPayments(); fetchStats(); });
    };

    const promoteUser = (userId: string) => {
        setPromoting(userId);
        authFetch(`${API_BASE}/admin/users/${userId}/promote`, { method: 'POST' })
            .then(r => r.json())
            .then(() => {
                fetchUsers();
                fetchStats();
                setPromoting(null);
            })
            .catch(() => setPromoting(null));
    };

    const demoteUser = (userId: string) => {
        setPromoting(userId);
        authFetch(`${API_BASE}/admin/users/${userId}/demote`, { method: 'POST' })
            .then(r => r.json())
            .then(() => {
                fetchUsers();
                fetchStats();
                setPromoting(null);
            })
            .catch(() => setPromoting(null));
    };

    const filteredUsers = users.filter(u => u.email?.toLowerCase().includes(searchQuery.toLowerCase()));

    return (
        <div className="admin-layout">
            <aside className="sidebar">
                <div className="brand-title">
                    <div className="brand-icon">
                        <ShieldCheck size={20} />
                    </div>
                    SOFTI ADMIN
                </div>

                <nav>
                    <a href="#" className={`nav-link ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}>
                        <LayoutDashboard className="nav-icon" />
                        Dashboard
                    </a>
                    <a href="#" className={`nav-link ${view === 'users' ? 'active' : ''}`} onClick={() => setView('users')}>
                        <UsersIcon className="nav-icon" />
                        Users
                    </a>
                    <a href="#" className={`nav-link ${view === 'payments' ? 'active' : ''}`} onClick={() => setView('payments')}>
                        <CreditCard className="nav-icon" />
                        Payments
                        {payments.length > 0 && (
                            <span style={{ marginLeft: 'auto', background: 'var(--primary)', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700 }}>
                                {payments.length}
                            </span>
                        )}
                    </a>
                </nav>

                <div className="user-profile-bottom">
                    <div className="avatar">A</div>
                    <div className="user-info">
                        <span className="user-name">Admin</span>
                        <span className="user-role">Superuser</span>
                    </div>
                    <div style={{ marginLeft: 'auto' }}>
                        <UserButton afterSignOutUrl="/" />
                    </div>
                </div>
            </aside>

            <main className="main-content">
                {view === 'dashboard' && (
                    <div className="animate-fade-in">
                        <div className="view-header">
                            <div>
                                <h1 className="view-title">Overview</h1>
                                <p className="view-subtitle">Welcome back. Here is what's happening today.</p>
                            </div>
                        </div>

                        <div className="stats-grid">
                            <div className="stat-card stagger-1 animate-fade-in">
                                <div className="stat-header">
                                    <span className="stat-label">Total Users</span>
                                    <div className="stat-icon-wrapper" style={{ color: 'var(--primary)', background: 'rgba(99,102,241,0.1)' }}>
                                        <UsersIcon size={24} />
                                    </div>
                                </div>
                                <div className="stat-value">{stats.total_users || 0}</div>
                            </div>

                            <div className="stat-card stagger-2 animate-fade-in">
                                <div className="stat-header">
                                    <span className="stat-label">Active PRO Users</span>
                                    <div className="stat-icon-wrapper" style={{ color: 'var(--success)', background: 'rgba(16,185,129,0.1)' }}>
                                        <CheckCircle size={24} />
                                    </div>
                                </div>
                                <div className="stat-value">{stats.pro_users || 0}</div>
                            </div>

                            <div className="stat-card stagger-3 animate-fade-in">
                                <div className="stat-header">
                                    <span className="stat-label">Pending Validations</span>
                                    <div className="stat-icon-wrapper" style={{ color: 'var(--warning)', background: 'rgba(245,158,11,0.1)' }}>
                                        <CreditCard size={24} />
                                    </div>
                                </div>
                                <div className="stat-value">{stats.pending_payments || 0}</div>
                            </div>
                        </div>
                    </div>
                )}

                {view === 'users' && (
                    <div className="animate-fade-in">
                        <div className="view-header">
                            <div>
                                <h1 className="view-title">User Management</h1>
                                <p className="view-subtitle">Manage all registered accounts and subscriptions.</p>
                            </div>
                        </div>

                        <div className="card-glass stagger-1 animate-fade-in">
                            <div className="table-header-controls">
                                <h2 className="table-title">All Users</h2>
                                <div className="search-input-wrapper">
                                    <Search className="search-icon" />
                                    <input
                                        type="text"
                                        className="input-search"
                                        placeholder="Search by email..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Email</th>
                                            <th>Plan</th>
                                            <th>Status</th>
                                            <th>Expires At</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredUsers.length === 0 ? (
                                            <tr>
                                                <td colSpan={5}>
                                                    <div className="empty-state">
                                                        <Inbox className="empty-icon" />
                                                        <div className="empty-title">No users found</div>
                                                        <p>Could not find any users matching your criteria.</p>
                                                    </div>
                                                </td>
                                            </tr>
                                        ) : filteredUsers.map(u => (
                                            <tr key={u.id}>
                                                <td>
                                                    <div className="user-cell">
                                                        <div className="user-cell-avatar">
                                                            <User size={16} />
                                                        </div>
                                                        {u.email}
                                                    </div>
                                                </td>
                                                <td>
                                                    <span className={`badge ${u.subscription.plan !== 'LITE' ? 'badge-pro' : 'badge-lite'}`}>
                                                        {u.subscription.plan}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className={`badge ${u.subscription.status === 'ACTIVE' ? 'badge-active' : 'badge-inactive'}`}>
                                                        {u.subscription.status}
                                                    </span>
                                                </td>
                                                <td style={{ color: 'var(--text-tertiary)' }}>{u.subscription.expires_at || 'Never'}</td>
                                                <td>
                                                    {u.subscription.plan === 'LITE' || u.subscription.plan === 'NONE' || !u.subscription.plan ? (
                                                        <button
                                                            className="btn-success"
                                                            onClick={() => promoteUser(u.id)}
                                                            disabled={promoting === u.id}
                                                        >
                                                            <ArrowUpCircle size={16} />
                                                            {promoting === u.id ? 'Promoting...' : 'Promote PRO'}
                                                        </button>
                                                    ) : (
                                                        <button
                                                            className="btn-danger"
                                                            onClick={() => demoteUser(u.id)}
                                                            disabled={promoting === u.id}
                                                        >
                                                            <ArrowDownCircle size={16} />
                                                            {promoting === u.id ? 'Demoting...' : 'Demote LITE'}
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {view === 'payments' && (
                    <div className="animate-fade-in">
                        <div className="view-header">
                            <div>
                                <h1 className="view-title">Pending Validations</h1>
                                <p className="view-subtitle">Review and approve pending manual payments.</p>
                            </div>
                        </div>

                        <div className="card-glass stagger-1 animate-fade-in">
                            <div className="table-header-controls">
                                <h2 className="table-title">Awaiting Approval</h2>
                            </div>
                            <div className="table-container">
                                {payments.length === 0 ? (
                                    <div className="empty-state">
                                        <CheckCircle className="empty-icon" style={{ color: 'var(--success)', opacity: 0.8 }} />
                                        <div className="empty-title">All caught up!</div>
                                        <p>There are no pending payments to review.</p>
                                    </div>
                                ) : (
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>User</th>
                                                <th>Method</th>
                                                <th>Amount</th>
                                                <th>Reference</th>
                                                <th>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {payments.map(p => (
                                                <tr key={p.id}>
                                                    <td>
                                                        <div className="user-cell">
                                                            <div className="user-cell-avatar">
                                                                <User size={16} />
                                                            </div>
                                                            {p.user_email}
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <span className="badge badge-lite">{p.method}</span>
                                                    </td>
                                                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>€{p.amount}</td>
                                                    <td>
                                                        <span className="reference-cell">{p.tx_reference}</span>
                                                    </td>
                                                    <td>
                                                        <button className="btn-success" onClick={() => verifyPayment(p.id)}>
                                                            <CheckCircle size={16} /> Approve
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default function App() {
    return (
        <div className="admin-wrapper" style={{ height: '100vh', width: '100vw' }}>
            <SignedIn>
                <AdminPanel />
            </SignedIn>
            <SignedOut>
                <RedirectToSignIn />
            </SignedOut>
        </div>
    );
}
