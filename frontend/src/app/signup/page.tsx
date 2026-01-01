'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/utils/AuthContext';

interface ValidationState {
    isValid: boolean;
    message: string;
}

export default function SignupPage() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    // Validation states
    const [emailValidation, setEmailValidation] = useState<ValidationState>({ isValid: true, message: '' });
    const [usernameValidation, setUsernameValidation] = useState<ValidationState>({ isValid: true, message: '' });
    const [passwordValidation, setPasswordValidation] = useState<ValidationState>({ isValid: true, message: '' });
    const [confirmValidation, setConfirmValidation] = useState<ValidationState>({ isValid: true, message: '' });

    const { signup, isAuthenticated, loading: authLoading } = useAuth();
    const router = useRouter();

    // Redirect if already logged in
    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            router.push('/');
        }
    }, [isAuthenticated, authLoading, router]);

    // Real-time email validation
    useEffect(() => {
        if (email === '') {
            setEmailValidation({ isValid: true, message: '' });
            return;
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setEmailValidation({ isValid: false, message: 'Enter a valid email address' });
        } else {
            setEmailValidation({ isValid: true, message: '✓ Valid email' });
        }
    }, [email]);

    // Real-time username validation
    useEffect(() => {
        if (username === '') {
            setUsernameValidation({ isValid: true, message: '' });
            return;
        }
        if (username.length < 3) {
            setUsernameValidation({ isValid: false, message: 'Username must be at least 3 characters' });
        } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            setUsernameValidation({ isValid: false, message: 'Only letters, numbers, and underscore allowed' });
        } else {
            setUsernameValidation({ isValid: true, message: '✓ Valid username' });
        }
    }, [username]);

    // Real-time password validation
    useEffect(() => {
        if (password === '') {
            setPasswordValidation({ isValid: true, message: '' });
            return;
        }
        const checks = [];
        if (password.length < 8) checks.push('8+ characters');
        if (!/[A-Z]/.test(password)) checks.push('uppercase letter');
        if (!/[a-z]/.test(password)) checks.push('lowercase letter');
        if (!/[0-9]/.test(password)) checks.push('number');

        if (checks.length > 0) {
            setPasswordValidation({ isValid: false, message: `Need: ${checks.join(', ')}` });
        } else {
            setPasswordValidation({ isValid: true, message: '✓ Strong password' });
        }
    }, [password]);

    // Real-time confirm password validation
    useEffect(() => {
        if (confirmPassword === '') {
            setConfirmValidation({ isValid: true, message: '' });
            return;
        }
        if (confirmPassword !== password) {
            setConfirmValidation({ isValid: false, message: 'Passwords do not match' });
        } else {
            setConfirmValidation({ isValid: true, message: '✓ Passwords match' });
        }
    }, [confirmPassword, password]);

    const isFormValid = () => {
        return email && username && password && confirmPassword &&
            emailValidation.isValid && emailValidation.message !== '' &&
            usernameValidation.isValid && usernameValidation.message !== '' &&
            passwordValidation.isValid && passwordValidation.message !== '' &&
            confirmValidation.isValid && confirmValidation.message !== '';
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!isFormValid()) {
            setError('Please fix all validation errors');
            return;
        }

        setLoading(true);

        try {
            await signup(email, username, password);
            setSuccess(true);
            setTimeout(() => {
                router.push('/login?registered=true');
            }, 2000);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const ValidationTooltip = ({ validation, show }: { validation: ValidationState; show: boolean }) => {
        if (!show || validation.message === '') return null;
        return (
            <div style={{
                position: 'absolute',
                right: '-8px',
                top: '50%',
                transform: 'translateX(100%) translateY(-50%)',
                background: validation.isValid ? '#1a3a36' : '#3a1a1a',
                border: `1px solid ${validation.isValid ? '#26a69a' : '#ef5350'}`,
                color: validation.isValid ? '#26a69a' : '#ef5350',
                fontSize: '0.65rem',
                padding: '4px 8px',
                borderRadius: '4px',
                whiteSpace: 'nowrap',
                zIndex: 10,
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
            }}>
                {validation.message}
                <div style={{
                    position: 'absolute',
                    left: '-4px',
                    top: '50%',
                    transform: 'translateY(-50%) rotate(45deg)',
                    width: '8px',
                    height: '8px',
                    background: validation.isValid ? '#1a3a36' : '#3a1a1a',
                    borderLeft: `1px solid ${validation.isValid ? '#26a69a' : '#ef5350'}`,
                    borderBottom: `1px solid ${validation.isValid ? '#26a69a' : '#ef5350'}`,
                }} />
            </div>
        );
    };

    return (
        <div style={{ maxWidth: '400px', margin: '60px auto', padding: '0 16px' }}>
            <div className="card">
                <div className="card-header" style={{ textAlign: 'center', fontSize: '1.25rem' }}>
                    Create Account
                </div>
                <div className="card-body">
                    {success ? (
                        <div style={{ textAlign: 'center', padding: '20px', color: 'var(--green)' }}>
                            ✓ Registration successful! Redirecting to login...
                        </div>
                    ) : (
                        <>
                            {error && (
                                <div style={{
                                    background: 'rgba(239, 83, 80, 0.15)',
                                    border: '1px solid var(--red)',
                                    color: 'var(--red)',
                                    padding: '12px',
                                    borderRadius: '4px',
                                    marginBottom: '16px',
                                    fontSize: '0.875rem'
                                }}>
                                    {error}
                                </div>
                            )}

                            <form onSubmit={handleSubmit}>
                                <div style={{ marginBottom: '16px', position: 'relative' }}>
                                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="input-field"
                                        placeholder="you@example.com"
                                        style={{ borderColor: email && !emailValidation.isValid ? 'var(--red)' : undefined }}
                                    />
                                    <ValidationTooltip validation={emailValidation} show={email !== ''} />
                                </div>

                                <div style={{ marginBottom: '16px', position: 'relative' }}>
                                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                                        Username
                                    </label>
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="input-field"
                                        placeholder="johndoe"
                                        style={{ borderColor: username && !usernameValidation.isValid ? 'var(--red)' : undefined }}
                                    />
                                    <ValidationTooltip validation={usernameValidation} show={username !== ''} />
                                </div>

                                <div style={{ marginBottom: '16px', position: 'relative' }}>
                                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                                        Password
                                    </label>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="input-field"
                                        placeholder="••••••••"
                                        style={{ borderColor: password && !passwordValidation.isValid ? 'var(--red)' : undefined }}
                                    />
                                    <ValidationTooltip validation={passwordValidation} show={password !== ''} />
                                </div>

                                <div style={{ marginBottom: '20px', position: 'relative' }}>
                                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                                        Confirm Password
                                    </label>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="input-field"
                                        placeholder="••••••••"
                                        style={{ borderColor: confirmPassword && !confirmValidation.isValid ? 'var(--red)' : undefined }}
                                    />
                                    <ValidationTooltip validation={confirmValidation} show={confirmPassword !== ''} />
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading || !isFormValid()}
                                    className="btn btn-primary"
                                    style={{ width: '100%', opacity: loading || !isFormValid() ? 0.6 : 1 }}
                                >
                                    {loading ? 'Creating account...' : 'Sign Up'}
                                </button>
                            </form>

                            <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '20px', fontSize: '0.875rem' }}>
                                Already have an account?{' '}
                                <Link href="/login" style={{ color: 'var(--blue)' }}>
                                    Login
                                </Link>
                            </p>
                        </>
                    )}
                </div>
            </div>

        </div>
    );
}
