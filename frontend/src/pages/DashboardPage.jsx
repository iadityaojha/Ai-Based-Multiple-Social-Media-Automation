import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { postsApi, keysApi } from '../api/client';

export default function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [keysStatus, setKeysStatus] = useState(null);
    const [upcoming, setUpcoming] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [statsRes, keysRes, upcomingRes] = await Promise.all([
                postsApi.getStats(),
                keysApi.getStatus(),
                postsApi.getUpcoming(),
            ]);
            setStats(statsRes.data);
            setKeysStatus(keysRes.data);
            setUpcoming(upcomingRes.data.posts || []);
        } catch (err) {
            console.error('Failed to load dashboard:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="spinner w-10 h-10"></div>
            </div>
        );
    }

    const needsSetup = keysStatus && !keysStatus.openai;

    return (
        <div className="space-y-8">
            {/* Welcome Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                <p className="text-gray-600 mt-1">Welcome to your AI Social Media Hub</p>
            </div>

            {/* Setup Alert */}
            {needsSetup && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                    <div className="flex items-start gap-4">
                        <span className="text-3xl">⚠️</span>
                        <div>
                            <h3 className="font-semibold text-yellow-800">Setup Required</h3>
                            <p className="text-yellow-700 mt-1">
                                Add your API keys to start generating content.
                            </p>
                            <Link
                                to="/settings"
                                className="btn btn-primary mt-4"
                            >
                                Go to Settings
                            </Link>
                        </div>
                    </div>
                </div>
            )}

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatsCard
                    icon="📝"
                    label="Drafts"
                    value={stats?.draft || 0}
                    color="gray"
                />
                <StatsCard
                    icon="⏰"
                    label="Scheduled"
                    value={stats?.pending || 0}
                    color="yellow"
                />
                <StatsCard
                    icon="✅"
                    label="Posted"
                    value={stats?.posted || 0}
                    color="green"
                />
                <StatsCard
                    icon="❌"
                    label="Failed"
                    value={stats?.failed || 0}
                    color="red"
                />
            </div>

            {/* Quick Actions */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Generate Card */}
                <div className="card card-hover">
                    <div className="flex items-center gap-4 mb-4">
                        <span className="text-4xl">✨</span>
                        <div>
                            <h3 className="text-lg font-semibold">Generate Content</h3>
                            <p className="text-gray-600 text-sm">Create AI-powered posts</p>
                        </div>
                    </div>
                    <Link to="/generate" className="btn btn-primary">
                        Start Generating
                    </Link>
                </div>

                {/* Posts Card */}
                <div className="card card-hover">
                    <div className="flex items-center gap-4 mb-4">
                        <span className="text-4xl">📋</span>
                        <div>
                            <h3 className="text-lg font-semibold">Manage Posts</h3>
                            <p className="text-gray-600 text-sm">View and schedule your content</p>
                        </div>
                    </div>
                    <Link to="/posts" className="btn btn-secondary">
                        View Posts
                    </Link>
                </div>
            </div>

            {/* API Keys Status */}
            <div className="card">
                <h3 className="font-semibold text-gray-900 mb-4">Connected Services</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <KeyStatusItem
                        name="OpenAI"
                        icon="🤖"
                        connected={keysStatus?.openai}
                    />
                    <KeyStatusItem
                        name="LinkedIn"
                        icon="💼"
                        connected={keysStatus?.linkedin}
                    />
                    <KeyStatusItem
                        name="Instagram"
                        icon="📸"
                        connected={keysStatus?.instagram}
                    />
                    <KeyStatusItem
                        name="Facebook"
                        icon="📘"
                        connected={keysStatus?.facebook}
                    />
                </div>
            </div>

            {/* Upcoming Posts */}
            {upcoming.length > 0 && (
                <div className="card">
                    <h3 className="font-semibold text-gray-900 mb-4">Upcoming Posts</h3>
                    <div className="space-y-3">
                        {upcoming.slice(0, 5).map((post) => (
                            <div
                                key={post.id}
                                className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
                            >
                                <div className="flex items-center gap-3">
                                    <PlatformBadge platform={post.platform} />
                                    <span className="text-sm text-gray-700 truncate max-w-xs">
                                        {post.content.slice(0, 60)}...
                                    </span>
                                </div>
                                <span className="text-xs text-gray-500">
                                    {new Date(post.scheduled_time).toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function StatsCard({ icon, label, value, color }) {
    const colors = {
        gray: 'bg-gray-100 text-gray-800',
        yellow: 'bg-yellow-100 text-yellow-800',
        green: 'bg-green-100 text-green-800',
        red: 'bg-red-100 text-red-800',
    };

    return (
        <div className="card">
            <div className="flex items-center gap-3">
                <span className="text-2xl">{icon}</span>
                <div>
                    <div className={`text-2xl font-bold ${colors[color].split(' ')[1]}`}>
                        {value}
                    </div>
                    <div className="text-sm text-gray-600">{label}</div>
                </div>
            </div>
        </div>
    );
}

function KeyStatusItem({ name, icon, connected }) {
    return (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
            <span className="text-xl">{icon}</span>
            <span className="text-sm font-medium">{name}</span>
            {connected ? (
                <span className="ml-auto text-green-500">✓</span>
            ) : (
                <span className="ml-auto text-gray-400">○</span>
            )}
        </div>
    );
}

function PlatformBadge({ platform }) {
    const config = {
        linkedin: { icon: '💼', bg: 'bg-blue-100 text-blue-800' },
        instagram: { icon: '📸', bg: 'bg-pink-100 text-pink-800' },
        facebook: { icon: '📘', bg: 'bg-indigo-100 text-indigo-800' },
    };
    const { icon, bg } = config[platform] || { icon: '📱', bg: 'bg-gray-100' };

    return (
        <span className={`px-2 py-1 rounded text-xs font-medium ${bg}`}>
            {icon} {platform}
        </span>
    );
}
