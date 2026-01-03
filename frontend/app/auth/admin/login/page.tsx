"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { Eye, EyeOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

export default function AdminLogin() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const formPayload = new FormData()
      formPayload.append("username", email)
      formPayload.append("password", password)

      const response = await api.postFormData("/auth/admin/login", formPayload)

      // Store token
      localStorage.setItem("token", response.access_token)
      localStorage.setItem("role", "admin")

      // Redirect to dashboard
      window.location.href = "/dashboard/admin"
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted px-4">
      <div className="w-full max-w-md">
        <div className="bg-card rounded-lg shadow-lg p-8 border border-border">
          {/* Logo Area */}
          <div className="text-center mb-8">
            <div className="bg-primary/10 rounded-lg p-4 mb-4 inline-block">
              <h1 className="text-2xl font-bold text-primary">Dayflow</h1>
            </div>
            <h2 className="text-2xl font-bold text-foreground">Admin Login</h2>
            <p className="text-muted-foreground text-sm mt-2">Human Resources Management</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 rounded text-destructive text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Email Address</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@company.com"
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
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded" />
                <span className="text-muted-foreground">Remember me</span>
              </label>
              <Link href="#" className="text-primary hover:underline">
                Forgot password?
              </Link>
            </div>

            {/* Sign In Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-2 rounded-lg transition"
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-border"></div>
            <span className="text-xs text-muted-foreground">OR</span>
            <div className="flex-1 h-px bg-border"></div>
          </div>

          {/* Employee Login Link */}
          <p className="text-center text-sm text-muted-foreground">
            Are you an employee?{" "}
            <Link href="/auth/employee/login" className="text-primary font-semibold hover:underline">
              Employee Login
            </Link>
          </p>
        </div>

        {/* Footer Info */}
        <p className="text-center text-xs text-muted-foreground mt-6">
          For HR and Admin personnel only. Secure authentication required.
        </p>
      </div>
    </div>
  )
}
