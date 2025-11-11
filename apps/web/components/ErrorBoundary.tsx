'use client'

import { Component, ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCcw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: {
    componentStack: string
  }
}

/**
 * Error Boundary component to catch and handle React errors gracefully.
 * 
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    // Log error to console (in production, send to error tracking service)
    console.error('ErrorBoundary caught error:', error, errorInfo)
    
    // Update state with error info
    this.setState({
      errorInfo: {
        componentStack: errorInfo.componentStack,
      },
    })
    
    // In production, send to error tracking service
    if (process.env.NODE_ENV === 'production') {
      // Example: Sentry.captureException(error, { contexts: { react: errorInfo } })
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full border-destructive">
            <CardHeader>
              <div className="flex items-center gap-3">
                <AlertCircle className="h-8 w-8 text-destructive" />
                <div>
                  <CardTitle>Something went wrong</CardTitle>
                  <CardDescription>
                    An unexpected error occurred while rendering this page
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {this.state.error && (
                <div className="p-4 bg-destructive/10 rounded-lg">
                  <p className="text-sm font-mono text-destructive">
                    {this.state.error.message}
                  </p>
                </div>
              )}
              
              {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                <details className="p-4 bg-muted rounded-lg">
                  <summary className="cursor-pointer text-sm font-medium mb-2">
                    Component Stack
                  </summary>
                  <pre className="text-xs overflow-auto max-h-64 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
              
              <div className="flex gap-3">
                <Button onClick={this.handleReset}>
                  <RefreshCcw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
                <Button variant="outline" onClick={() => window.location.href = '/'}>
                  Go Home
                </Button>
              </div>
              
              <p className="text-sm text-muted-foreground">
                If this problem persists, please{' '}
                <a href="/contact" className="text-primary hover:underline">
                  contact support
                </a>{' '}
                or{' '}
                <a href="/_debug" className="text-primary hover:underline">
                  check the debug page
                </a>
                .
              </p>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

