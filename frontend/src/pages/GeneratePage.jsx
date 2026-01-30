import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateApi, postsApi } from '../api/client';

const PLATFORMS = [
    { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: 'bg-blue-100 border-blue-500' },
    { id: 'instagram', name: 'Instagram', icon: '📸', color: 'bg-pink-100 border-pink-500' },
    { id: 'facebook', name: 'Facebook', icon: '📘', color: 'bg-indigo-100 border-indigo-500' },
];

const TONES = [
    { id: 'professional', name: 'Professional', icon: '💼' },
    { id: 'casual', name: 'Casual', icon: '😊' },
    { id: 'educational', name: 'Educational', icon: '📚' },
    { id: 'inspirational', name: 'Inspirational', icon: '⭐' },
];

export default function GeneratePage() {
    const [topic, setTopic] = useState('');
    const [context, setContext] = useState('');
    const [platforms, setPlatforms] = useState(['linkedin', 'instagram', 'facebook']);
    const [tone, setTone] = useState('professional');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [generated, setGenerated] = useState(null);
    const [approving, setApproving] = useState({});
    const navigate = useNavigate();

    const togglePlatform = (id) => {
        setPlatforms((prev) =>
            prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
        );
    };

    const handleGenerate = async (e) => {
        e.preventDefault();
        if (!topic.trim() || platforms.length === 0) {
            setError('Please enter a topic and select at least one platform');
            return;
        }

        setError('');
        setLoading(true);
        setGenerated(null);

        try {
            const res = await generateApi.generate({
                topic,
                platforms,
                tone,
                additional_context: context || undefined,
            });
            setGenerated(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to generate content');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (postId, scheduledTime = null) => {
        setApproving((prev) => ({ ...prev, [postId]: true }));
        try {
            await postsApi.approve(postId, { scheduled_time: scheduledTime });
            // Update UI
            setGenerated((prev) => ({
                ...prev,
                posts: prev.posts.map((p) =>
                    p.post_id === postId ? { ...p, status: 'pending' } : p
                ),
            }));
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to approve');
        } finally {
            setApproving((prev) => ({ ...prev, [postId]: false }));
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Generate Content</h1>
                <p className="text-gray-600 mt-1">Create AI-powered posts for your social media</p>
            </div>

            {/* Form */}
            <form onSubmit={handleGenerate} className="card space-y-6">
                {/* Topic */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Topic *
                    </label>
                    <input
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        className="input"
                        placeholder="e.g., Introduction to Machine Learning"
                        required
                    />
                </div>

                {/* Additional Context */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Additional Context
                    </label>
                    <textarea
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        className="input h-24"
                        placeholder="Any specific points, examples, or focus areas..."
                    />
                </div>

                {/* Platforms */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                        Platforms *
                    </label>
                    <div className="flex flex-wrap gap-3">
                        {PLATFORMS.map(({ id, name, icon, color }) => (
                            <button
                                key={id}
                                type="button"
                                onClick={() => togglePlatform(id)}
                                className={`px-4 py-3 rounded-xl border-2 transition-all flex items-center gap-2 ${platforms.includes(id)
                                        ? `${color} border-current`
                                        : 'bg-gray-50 border-gray-200 text-gray-500'
                                    }`}
                            >
                                <span className="text-xl">{icon}</span>
                                <span className="font-medium">{name}</span>
                                {platforms.includes(id) && <span className="text-green-600">✓</span>}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Tone */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                        Tone
                    </label>
                    <div className="flex flex-wrap gap-2">
                        {TONES.map(({ id, name, icon }) => (
                            <button
                                key={id}
                                type="button"
                                onClick={() => setTone(id)}
                                className={`px-4 py-2 rounded-lg transition-all ${tone === id
                                        ? 'bg-primary-100 text-primary-700 font-medium'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                            >
                                {icon} {name}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                        {error}
                    </div>
                )}

                {/* Submit */}
                <button
                    type="submit"
                    disabled={loading}
                    className="btn btn-primary w-full py-3 text-lg"
                >
                    {loading ? (
                        <>
                            <span className="spinner w-5 h-5"></span>
                            Generating...
                        </>
                    ) : (
                        <>
                            ✨ Generate Content
                        </>
                    )}
                </button>
            </form>

            {/* Generated Content */}
            {generated && (
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-gray-900">
                        Generated Content for "{generated.topic_name}"
                    </h2>

                    <div className="space-y-4">
                        {generated.posts.map((post) => (
                            <PostPreviewCard
                                key={post.post_id}
                                post={post}
                                onApprove={handleApprove}
                                approving={approving[post.post_id]}
                            />
                        ))}
                    </div>

                    <div className="flex justify-center">
                        <button
                            onClick={() => navigate('/posts')}
                            className="btn btn-secondary"
                        >
                            View All Posts →
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

function PostPreviewCard({ post, onApprove, approving }) {
    const [showSchedule, setShowSchedule] = useState(false);
    const [scheduleTime, setScheduleTime] = useState('');

    const platformConfig = {
        linkedin: { icon: '💼', name: 'LinkedIn', bg: 'bg-blue-50' },
        instagram: { icon: '📸', name: 'Instagram', bg: 'bg-pink-50' },
        facebook: { icon: '📘', name: 'Facebook', bg: 'bg-indigo-50' },
    };

    const config = platformConfig[post.platform] || { icon: '📱', name: post.platform, bg: 'bg-gray-50' };
    const isApproved = post.status === 'pending' || post.status === 'posted';

    return (
        <div className={`card ${config.bg} border-l-4 border-current`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <span className="text-2xl">{config.icon}</span>
                    <span className="font-semibold text-gray-900">{config.name}</span>
                </div>
                <span className={`badge badge-${post.status}`}>
                    {post.status}
                </span>
            </div>

            {/* Content */}
            <div className="bg-white rounded-lg p-4 mb-4">
                <p className="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed">
                    {post.content}
                </p>
                {post.hashtags?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                        {post.hashtags.map((tag, i) => (
                            <span key={i} className="text-primary-600 text-xs">
                                {tag}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Actions */}
            {!isApproved && (
                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={() => onApprove(post.post_id)}
                        disabled={approving}
                        className="btn btn-primary"
                    >
                        {approving ? (
                            <span className="spinner w-4 h-4"></span>
                        ) : (
                            '✓ Approve Now'
                        )}
                    </button>
                    <button
                        onClick={() => setShowSchedule(!showSchedule)}
                        className="btn btn-secondary"
                    >
                        📅 Schedule
                    </button>
                </div>
            )}

            {/* Schedule Picker */}
            {showSchedule && !isApproved && (
                <div className="mt-4 flex gap-2">
                    <input
                        type="datetime-local"
                        value={scheduleTime}
                        onChange={(e) => setScheduleTime(e.target.value)}
                        className="input flex-1"
                    />
                    <button
                        onClick={() => {
                            if (scheduleTime) {
                                onApprove(post.post_id, new Date(scheduleTime).toISOString());
                                setShowSchedule(false);
                            }
                        }}
                        className="btn btn-primary"
                    >
                        Schedule
                    </button>
                </div>
            )}
        </div>
    );
}
