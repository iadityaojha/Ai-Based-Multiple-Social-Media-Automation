import { NavLink, Outlet } from 'react-router-dom';

const navLinks = [
    { to: '/', label: 'Dashboard', icon: '📊' },
    { to: '/generate', label: 'AI Generate', icon: '✨' },
    { to: '/manual', label: 'Manual Post', icon: '✍️' },
    { to: '/posts', label: 'Posts', icon: '📝' },
    { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Layout() {
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        {/* Logo */}
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">🚀</span>
                            <h1 className="text-xl font-bold text-gray-900">AI Social</h1>
                        </div>

                        {/* Nav */}
                        <nav className="hidden md:flex items-center gap-1">
                            {navLinks.map(({ to, label, icon }) => (
                                <NavLink
                                    key={to}
                                    to={to}
                                    end={to === '/'}
                                    className={({ isActive }) =>
                                        `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                            ? 'bg-primary-100 text-primary-700'
                                            : 'text-gray-600 hover:bg-gray-100'
                                        }`
                                    }
                                >
                                    <span className="mr-2">{icon}</span>
                                    {label}
                                </NavLink>
                            ))}
                        </nav>

                        {/* Status */}
                        <div className="text-sm text-gray-500">
                            Single-User Mode
                        </div>
                    </div>
                </div>

                {/* Mobile Nav */}
                <div className="md:hidden border-t border-gray-200">
                    <div className="flex overflow-x-auto px-4 py-2 gap-2">
                        {navLinks.map(({ to, label, icon }) => (
                            <NavLink
                                key={to}
                                to={to}
                                end={to === '/'}
                                className={({ isActive }) =>
                                    `flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${isActive
                                        ? 'bg-primary-100 text-primary-700'
                                        : 'text-gray-600 bg-gray-100'
                                    }`
                                }
                            >
                                {icon} {label}
                            </NavLink>
                        ))}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <Outlet />
            </main>
        </div>
    );
}
