import { useState, useEffect } from 'react';
import { keysApi } from '../api/client';

const API_KEY_TYPES = [
    {
        id: 'openai',
        name: 'OpenAI',
        icon: '🤖',
        description: 'For AI content generation (GPT-4)',
        placeholder: 'sk-...',
        link: 'https://platform.openai.com/api-keys',
    },
    {
        id: 'gemini',
        name: 'Google Gemini',
        icon: '✨',
        description: 'For AI content generation (free tier available)',
        placeholder: 'AIza...',
        link: 'https://aistudio.google.com/app/apikey',
    },
    {
        id: 'linkedin',
        name: 'LinkedIn',
        icon: '💼',
        description: 'For auto-posting to LinkedIn',
        placeholder: 'Access token',
        link: 'https://www.linkedin.com/developers/',
    },
    {
        id: 'instagram',
        name: 'Instagram',
        icon: '📸',
        description: 'For auto-posting to Instagram',
        placeholder: 'Access token',
        link: 'https://developers.facebook.com/',
    },
    {
        id: 'facebook',
        name: 'Facebook',
        icon: '📘',
        description: 'For auto-posting to Facebook',
        placeholder: 'Page access token',
        link: 'https://developers.facebook.com/',
    },
];

export default function SettingsPage() {
    const [keys, setKeys] = useState([]);
    const [keysStatus, setKeysStatus] = useState({});
    const [loading, setLoading] = useState(true);
    const [editingKey, setEditingKey] = useState(null);
    const [newKeyValue, setNewKeyValue] = useState('');
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [keysRes, statusRes] = await Promise.all([
                keysApi.list(),
                keysApi.getStatus(),
            ]);
            setKeys(keysRes.data);
            setKeysStatus(statusRes.data);
        } catch (err) {
            console.error('Failed to load keys:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveKey = async (keyType) => {
        if (!newKeyValue.trim()) return;

        setSaving(true);
        try {
            // Check if key exists
            const existingKey = keys.find((k) => k.key_type === keyType);

            if (existingKey) {
                await keysApi.update(existingKey.id, { api_key: newKeyValue });
            } else {
                await keysApi.create({ key_type: keyType, api_key: newKeyValue });
            }

            setEditingKey(null);
            setNewKeyValue('');
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to save key');
        } finally {
            setSaving(false);
        }
    };

    const handleTestKey = async (keyId) => {
        setTesting(keyId);
        try {
            const res = await keysApi.test(keyId);
            alert(res.data.message);
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Test failed');
        } finally {
            setTesting(null);
        }
    };

    const handleDeleteKey = async (keyId) => {
        if (!confirm('Are you sure you want to delete this API key?')) return;

        try {
            await keysApi.delete(keyId);
            await loadData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to delete key');
        }
    };

    const getKeyForType = (type) => keys.find((k) => k.key_type === type);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="spinner w-10 h-10"></div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
                <p className="text-gray-600 mt-1">Manage your API keys and preferences</p>
            </div>

            {/* API Keys Section */}
            <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">API Keys</h2>
                <p className="text-gray-600 text-sm mb-6">
                    Your API keys are encrypted and stored securely. You control your own keys.
                </p>

                <div className="space-y-4">
                    {API_KEY_TYPES.map((keyConfig) => {
                        const existingKey = getKeyForType(keyConfig.id);
                        const isConfigured = keysStatus[keyConfig.id];
                        const isEditing = editingKey === keyConfig.id;

                        return (
                            <div
                                key={keyConfig.id}
                                className={`p-4 rounded-xl border-2 transition-all ${isConfigured
                                    ? 'border-green-200 bg-green-50'
                                    : 'border-gray-200 bg-gray-50'
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3">
                                        <span className="text-2xl">{keyConfig.icon}</span>
                                        <div>
                                            <div className="font-semibold text-gray-900 flex items-center gap-2">
                                                {keyConfig.name}
                                                {isConfigured && (
                                                    <span className="text-green-600 text-sm">✓ Connected</span>
                                                )}
                                            </div>
                                            <div className="text-sm text-gray-600">{keyConfig.description}</div>
                                            {existingKey && (
                                                <div className="text-xs text-gray-500 mt-1">
                                                    Key: {existingKey.masked_key}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <a
                                        href={keyConfig.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-primary-600 hover:underline"
                                    >
                                        Get key →
                                    </a>
                                </div>

                                {/* Edit Form */}
                                {isEditing ? (
                                    <div className="mt-4 space-y-3">
                                        <input
                                            type="password"
                                            value={newKeyValue}
                                            onChange={(e) => setNewKeyValue(e.target.value)}
                                            className="input"
                                            placeholder={keyConfig.placeholder}
                                            autoFocus
                                        />
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleSaveKey(keyConfig.id)}
                                                disabled={saving}
                                                className="btn btn-primary"
                                            >
                                                {saving ? 'Saving...' : 'Save Key'}
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setEditingKey(null);
                                                    setNewKeyValue('');
                                                }}
                                                className="btn btn-secondary"
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="mt-4 flex flex-wrap gap-2">
                                        <button
                                            onClick={() => setEditingKey(keyConfig.id)}
                                            className="btn btn-secondary text-sm"
                                        >
                                            {existingKey ? '✏️ Update' : '➕ Add Key'}
                                        </button>
                                        {existingKey && (
                                            <>
                                                <button
                                                    onClick={() => handleTestKey(existingKey.id)}
                                                    disabled={testing === existingKey.id}
                                                    className="btn btn-outline text-sm"
                                                >
                                                    {testing === existingKey.id ? 'Testing...' : '🔍 Test'}
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteKey(existingKey.id)}
                                                    className="btn btn-outline text-sm text-red-600 border-red-200 hover:bg-red-50"
                                                >
                                                    🗑 Remove
                                                </button>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Security Note */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                <h3 className="font-semibold text-blue-900 flex items-center gap-2">
                    🔒 Security
                </h3>
                <ul className="mt-3 text-sm text-blue-800 space-y-2">
                    <li>• All API keys are encrypted before storage using AES-256</li>
                    <li>• Keys are never logged or exposed in responses</li>
                    <li>• Each user has isolated, encrypted storage</li>
                    <li>• You can delete your keys at any time</li>
                </ul>
            </div>
        </div>
    );
}
