import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { manualPostApi } from '../api/client';

const PLATFORMS = [
    { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: 'bg-blue-100 border-blue-500 text-blue-700' },
    { id: 'instagram', name: 'Instagram', icon: '📸', color: 'bg-pink-100 border-pink-500 text-pink-700' },
    { id: 'facebook', name: 'Facebook', icon: '📘', color: 'bg-indigo-100 border-indigo-500 text-indigo-700' },
];

export default function ManualPostPage() {
    const navigate = useNavigate();
    const fileInputRef = useRef(null);

    const [content, setContent] = useState('');
    const [selectedPlatforms, setSelectedPlatforms] = useState(['linkedin']);
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [uploadedFilename, setUploadedFilename] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [posting, setPosting] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [results, setResults] = useState([]);

    const togglePlatform = (id) => {
        setSelectedPlatforms(prev =>
            prev.includes(id)
                ? prev.filter(p => p !== id)
                : [...prev, id]
        );
    };

    const handleImageSelect = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            setError('Please select an image file');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            setError('Image size must be less than 10MB');
            return;
        }

        setImageFile(file);
        setImagePreview(URL.createObjectURL(file));
        setError('');

        // Upload the image
        setUploading(true);
        try {
            const res = await manualPostApi.uploadImage(file);
            setUploadedFilename(res.data.filename);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to upload image');
            setImageFile(null);
            setImagePreview(null);
        } finally {
            setUploading(false);
        }
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file && file.type.startsWith('image/')) {
            handleImageSelect({ target: { files: [file] } });
        }
    }, []);

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const removeImage = () => {
        setImageFile(null);
        setImagePreview(null);
        setUploadedFilename(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handlePost = async () => {
        if (!content.trim()) {
            setError('Please enter some content');
            return;
        }

        if (selectedPlatforms.length === 0) {
            setError('Please select at least one platform');
            return;
        }

        setPosting(true);
        setError('');
        setSuccess('');
        setResults([]);

        try {
            const res = await manualPostApi.create({
                content: content.trim(),
                platforms: selectedPlatforms,
                imageFilename: uploadedFilename,
            });

            setSuccess(res.data.message);
            setResults(res.data.posts || []);

            // Clear form on success
            if (res.data.success) {
                setTimeout(() => {
                    navigate('/posts');
                }, 2000);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create post');
        } finally {
            setPosting(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">✍️ Manual Post</h1>
                <p className="text-gray-600 mt-1">
                    Write or paste your own content and post to multiple platforms
                </p>
            </div>

            {/* Alerts */}
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
                    {error}
                </div>
            )}

            {success && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl">
                    {success}
                </div>
            )}

            {/* Main Form */}
            <div className="card space-y-6">
                {/* Content Input */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Post Content
                    </label>
                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        className="input min-h-[200px] resize-y"
                        placeholder="Write or paste your post content here...

You can include hashtags, mentions, and emojis! 🚀"
                    />
                    <div className="flex justify-between mt-2 text-sm text-gray-500">
                        <span>{content.length} characters</span>
                        <span>
                            {content.length > 3000 && <span className="text-red-500">LinkedIn max: 3000</span>}
                            {content.length > 2200 && content.length <= 3000 && <span className="text-yellow-500">Instagram max: 2200</span>}
                        </span>
                    </div>
                </div>

                {/* Image Upload */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Image (Optional)
                    </label>

                    {!imagePreview ? (
                        <div
                            onClick={() => fileInputRef.current?.click()}
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-50 transition-colors"
                        >
                            <div className="text-4xl mb-2">📷</div>
                            <p className="text-gray-600">
                                Click to upload or drag & drop an image
                            </p>
                            <p className="text-sm text-gray-400 mt-1">
                                PNG, JPG, GIF up to 10MB
                            </p>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                onChange={handleImageSelect}
                                className="hidden"
                            />
                        </div>
                    ) : (
                        <div className="relative">
                            <img
                                src={imagePreview}
                                alt="Preview"
                                className="w-full max-h-80 object-contain rounded-xl border"
                            />
                            <button
                                onClick={removeImage}
                                className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-2 hover:bg-red-600"
                                title="Remove image"
                            >
                                ✕
                            </button>
                            {uploading && (
                                <div className="absolute inset-0 bg-black/50 flex items-center justify-center rounded-xl">
                                    <div className="spinner w-8 h-8 text-white"></div>
                                </div>
                            )}
                            {uploadedFilename && !uploading && (
                                <div className="absolute bottom-2 left-2 bg-green-500 text-white px-3 py-1 rounded-full text-sm">
                                    ✓ Uploaded
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Platform Selection */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Post to Platforms
                    </label>
                    <div className="flex flex-wrap gap-3">
                        {PLATFORMS.map((platform) => (
                            <button
                                key={platform.id}
                                onClick={() => togglePlatform(platform.id)}
                                className={`px-4 py-3 rounded-xl border-2 font-medium transition-all ${selectedPlatforms.includes(platform.id)
                                        ? platform.color + ' border-2'
                                        : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                <span className="mr-2">{platform.icon}</span>
                                {platform.name}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4 pt-4">
                    <button
                        onClick={handlePost}
                        disabled={posting || !content.trim() || selectedPlatforms.length === 0}
                        className="btn btn-primary flex-1"
                    >
                        {posting ? (
                            <>
                                <span className="spinner w-5 h-5 mr-2"></span>
                                Posting...
                            </>
                        ) : (
                            <>🚀 Post Now</>
                        )}
                    </button>
                </div>
            </div>

            {/* Results */}
            {results.length > 0 && (
                <div className="card">
                    <h3 className="font-semibold text-lg mb-4">Posting Results</h3>
                    <div className="space-y-3">
                        {results.map((result, idx) => (
                            <div
                                key={idx}
                                className={`flex items-center justify-between p-3 rounded-lg ${result.success ? 'bg-green-50' : 'bg-red-50'
                                    }`}
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-xl">
                                        {PLATFORMS.find(p => p.id === result.platform)?.icon}
                                    </span>
                                    <span className="font-medium capitalize">
                                        {result.platform}
                                    </span>
                                </div>
                                <div className={`text-sm ${result.success ? 'text-green-700' : 'text-red-700'}`}>
                                    {result.success ? '✓ ' : '✕ '}{result.message}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
