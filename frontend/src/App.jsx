import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Pages
import DashboardPage from './pages/DashboardPage';
import GeneratePage from './pages/GeneratePage';
import ManualPostPage from './pages/ManualPostPage';
import PostsPage from './pages/PostsPage';
import SettingsPage from './pages/SettingsPage';

// Layout
import Layout from './components/Layout';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* All routes are now public - no login required */}
                <Route path="/" element={<Layout />}>
                    <Route index element={<DashboardPage />} />
                    <Route path="generate" element={<GeneratePage />} />
                    <Route path="manual" element={<ManualPostPage />} />
                    <Route path="posts" element={<PostsPage />} />
                    <Route path="settings" element={<SettingsPage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;

