"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { Eye, EyeOff, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

export default function HRSignup() {
    const [formData, setFormData] = useState({
        companyName: "",
        name: "",
        email: "",
        phone: "",
        password: "",
        confirmPassword: "",
    })
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)
    const [logoFile, setLogoFile] = useState<File | null>(null)

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setFormData((prev) => ({ ...prev, [name]: value }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")

        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match")
            return
        }

        if (formData.password.length < 8) {
            setError("Password must be at least 8 characters")
            return
        }

        setLoading(true)
        try {
            const formPayload = new FormData()
            formPayload.append("email", formData.email)
            formPayload.append("password", formData.password)
            formPayload.append("company_name", formData.companyName)
            formPayload.append("full_name", formData.name)
            formPayload.append("phone", formData.phone)

            if (logoFile) {
                formPayload.append("logo", logoFile)
            }

            await api.postFormData("/auth/hr/register", formPayload)

            // Redirect to login on success
            window.location.href = "/auth/hr/login"
        } catch (err: any) {
            setError(err.message || "Registration failed. Please try again.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted px-4 py-8">
            <div className="w-full max-w-lg">
                <div className="bg-card rounded-lg shadow-lg p-8 border border-border">
                    {/* Logo Area */}
                    <div className="text-center mb-8">
                        <div className="bg-primary/10 rounded-lg p-4 mb-4 inline-block">
                            <h1 className="text-2xl font-bold text-primary">Dayflow</h1>
                        </div>
                        <h2 className="text-2xl font-bold text-foreground">HR Registration</h2>
                        <p className="text-muted-foreground text-sm mt-2">Set up your HR management account</p>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 rounded text-destructive text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Company Name */}
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Company Name</label>
                            <Input
                                type="text"
                                name="companyName"
                                value={formData.companyName}
                                onChange={handleChange}
                                placeholder="Your Company Name"
                                required
                                className="w-full"
                            />
                        </div>

                        {/* Logo Upload */}
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Company Logo</label>
                            <div className="border-2 border-dashed border-border rounded-lg p-4 cursor-pointer hover:border-primary transition">
                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                                    className="hidden"
                                    id="logo-upload"
                                />
                                <label htmlFor="logo-upload" className="flex items-center justify-center gap-2 cursor-pointer">
                                    <Upload className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-sm text-muted-foreground">
                                        {logoFile ? logoFile.name : "Click to upload logo"}
                                    </span>
                                </label>
                            </div>
                        </div>

                        {/* Full Name */}
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Full Name</label>
                            <Input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="Your Name"
                                required
                                className="w-full"
                            />
                        </div>

                        {/* Email */}
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Email Address</label>
                            <Input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="hr@company.com"
                                required
                                className="w-full"
                            />
                        </div>

                        {/* Phone */}
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Phone Number</label>
                            <Input
                                type="tel"
                                name="phone"
                                value={formData.phone}
                                onChange={handleChange}
                                placeholder="+1 (555) 000-0000"
                                required
                                className="w-full"
                            />
                        </div>

                        {/* Password */}
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Password</label>
                            <div className="relative">
                                <Input
                                    type={showPassword ? "text" : "password"}
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    placeholder="••••••••"
                                    required
                                    className="w-full pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">At least 8 characters</p>
                        </div>

                        {/* Confirm Password */}
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Confirm Password</label>
                            <div className="relative">
                                <Input
                                    type={showConfirmPassword ? "text" : "password"}
                                    name="confirmPassword"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    placeholder="••••••••"
                                    required
                                    className="w-full pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                >
                                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        {/* Sign Up Button */}
                        <Button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-2 rounded-lg transition"
                        >
                            {loading ? "Creating account..." : "Sign Up"}
                        </Button>
                    </form>

                    {/* Login Link */}
                    <p className="text-center text-sm text-muted-foreground mt-6">
                        Already have an account?{" "}
                        <Link href="/auth/hr/login" className="text-primary font-semibold hover:underline">
                            Sign In
                        </Link>
                    </p>
                </div>

                {/* Footer Info */}
                <div className="mt-6 p-4 bg-card/50 border border-border rounded-lg">
                    <p className="text-xs text-muted-foreground">
                        <strong>Note:</strong> HR Officers can manage employee records but have restricted access compared to Admins.
                    </p>
                </div>
            </div>
        </div>
    )
}
