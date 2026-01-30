import { useState, useEffect } from 'react';
import { postsApi } from '../api/client';

export default function PostsPage() {
    const [posts, setPosts] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [actionLoading, setActionLoading] = useState({});

    useEffect(() => {
        loadData();
    }, [filter]);

    const loadData = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filter !== 'all') params.status_filter = filter;

            const [postsRes, statsRes] = await Promise.all([
                postsApi.list(params),
                postsApi.getStats(),
            ]);
            setPosts(postsRes.data.posts || []);
            setStats(statsRes.data);
        } catch (err) {
            console.error('Failed to load posts:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async (postId, action) => {
        setActionLoading((prev) => ({ ...prev, [postId]: action }));
        try {
            if (action === 'cancel') {
                await postsApi.cancel(postId);
            } else if (action === 'retry') {
                await postsApi.retry(postId);
            } else if (action === 'delete') {
                if (confirm('Are you sure you want to delete this post?')) {
                    await postsApi.delete(postId);
                }
            }
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Action failed');
        } finally {
            setActionLoading((prev) => ({ ...prev, [postId]: null }));
        }
    };

    const filters = [
        { id: 'all', label: 'All', count: stats?.total },
        { id: 'draft', label: 'Drafts', count: stats?.draft },
        { id: 'pending', label: 'Scheduled', count: stats?.pending },
        { id: 'posted', label: 'Posted', count: stats?.posted },
        { id: 'failed', label: 'Failed', count: stats?.failed },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Posts</h1>
                    <p className="text-gray-600 mt-1">Manage your scheduled and published content</p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-2">
                {filters.map(({ id, label, count }) => (
                    <button
                        key={id}
                        onClick={() => setFilter(id)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === id
                                ? 'bg-primary-100 text-primary-700'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                    >
                        {label}
                        {count !== undefined && (
                            <span className="ml-2 px-1.5 py-0.5 bg-white rounded-full text-xs">
                                {count}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* Posts List */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="spinner w-10 h-10"></div>
                </div>
            ) : posts.length === 0 ? (
                <div className="card text-center py-12">
                    <span className="text-5xl">📭</span>
                    <h3 className="text-lg font-semibold text-gray-900 mt-4">No posts found</h3>
                    <p className="text-gray-600 mt-2">
                        {filter === 'all'
                            ? 'Generate some content to get started'
                            : `No ${filter} posts right now`}
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {posts.map((post) => (
                        <PostCard
                            key={post.id}
                            post={post}
                            onAction={handleAction}
                            actionLoading={actionLoading[post.id]}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

function PostCard({ post, onAction, actionLoading }) {
    const [expanded, setExpanded] = useState(false);

    const platformConfig = {
        linkedin: { icon: '💼', name: 'LinkedIn', color: 'text-blue-600' },
        instagram: { icon: '📸', name: 'Instagram', color: 'text-pink-600' },
        facebook: { icon: '📘', name: 'Facebook', color: 'text-indigo-600' },
    };

    const config = platformConfig[post.platform] || { icon: '📱', name: post.platform, color: 'text-gray-600' };

    const formatDate = (dateStr) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString();
    };

    return (
        <div className="card">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{config.icon}</span>
                    <div>
                        <div className="font-semibold text-gray-900">{config.name}</div>
                        <div className="text-xs text-gray-500">
                            Topic: {post.topic_name}
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`badge badge-${post.status}`}>
                        {post.status}
                    </span>
                </div>
            </div>

            {/* Content Preview */}
            <div
                className={`mt-4 text-gray-700 text-sm ${expanded ? '' : 'line-clamp-3'
                    }`}
            >
                {post.content}
            </div>
            {post.content.length > 200 && (
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-primary-600 text-sm mt-2 hover:underline"
                >
                    {expanded ? 'Show less' : 'Show more'}
                </button>
            )}

            {/* Meta */}
            <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
                {post.scheduled_time && (
                    <div>
                        📅 Scheduled: {formatDate(post.scheduled_time)}
                    </div>
                )}
                {post.posted_at && (
                    <div>
                        ✅ Posted: {formatDate(post.posted_at)}
                    </div>
                )}
                <div>🎨 Tone: {post.tone}</div>
            </div>

            {/* Error */}
            {post.last_error && (
                <div className="mt-3 p-3 bg-red-50 rounded-lg text-sm text-red-700">
                    ⚠️ {post.last_error}
                </div>
            )}

            {/* Actions */}
            <div className="mt-4 flex flex-wrap gap-2 pt-4 border-t border-gray-100">
                {post.status === 'pending' && (
                    <button
                        onClick={() => onAction(post.id, 'cancel')}
                        disabled={actionLoading}
                        className="btn btn-secondary text-sm"
                    >
                        {actionLoading === 'cancel' ? 'Canceling...' : '✕ Cancel'}
                    </button>
                )}
                {post.status === 'failed' && (
                    <button
                        onClick={() => onAction(post.id, 'retry')}
                        disabled={actionLoading}
                        className="btn btn-primary text-sm"
                    >
                        {actionLoading === 'retry' ? 'Retrying...' : '↻ Retry'}
                    </button>
                )}
                {post.status !== 'posted' && (
                    <button
                        onClick={() => onAction(post.id, 'delete')}
                        disabled={actionLoading}
                        className="btn btn-outline text-sm text-red-600 border-red-200 hover:bg-red-50"
                    >
                        🗑 Delete
                    </button>
                )}
            </div>
        </div>
    );
}
