'use client'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Users, Brain, Scale, Sparkles, ArrowLeft, Plus, X, Loader2, CheckCircle2, Star } from 'lucide-react'
import { useState, useEffect } from 'react'
import { 
  getTopics, 
  createTopic, 
  getTopic, 
  createArgument, 
  verifyArgument,
  type TopicListItem,
  type TopicDetailResponse,
  type ArgumentCreate
} from '@/src/api'

export default function Home() {
  const [view, setView] = useState<'landing' | 'browse' | 'topic' | 'createDebate'>('landing')
  const [topics, setTopics] = useState<TopicListItem[]>([])
  const [selectedTopic, setSelectedTopic] = useState<TopicDetailResponse | null>(null)
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newDebateForm, setNewDebateForm] = useState({
    title: '',
    createdBy: 'user', // Default username - could be made dynamic
    proArgs: [{ title: '', content: '', sources: '' }],
    conArgs: [{ title: '', content: '', sources: '' }]
  })
  const [showAddArgumentForm, setShowAddArgumentForm] = useState<{ side: 'pro' | 'con' | null }>({ side: null })
  const [newArgument, setNewArgument] = useState<{ title: '', content: '', sources: '', side: 'pro' | 'con' }>({
    title: '',
    content: '',
    sources: '',
    side: 'pro'
  })
  const [verifyingArgumentId, setVerifyingArgumentId] = useState<number | null>(null)

  const fetchTopics = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getTopics()
      setTopics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch topics')
      console.error('Error fetching topics:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchTopicDetails = async (topicId: number) => {
    setLoading(true)
    setError(null)
    try {
      // Backend now automatically verifies and sorts by validity
      const data = await getTopic(topicId)
      setSelectedTopic(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch topic details')
      console.error('Error fetching topic details:', err)
    } finally {
      setLoading(false)
    }
  }

  // Fetch topics when browse view is opened
  useEffect(() => {
    if (view === 'browse') {
      fetchTopics()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view])

  // Fetch topic details when a topic is selected
  useEffect(() => {
    if (selectedTopicId !== null) {
      fetchTopicDetails(selectedTopicId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTopicId])

  const handleStartDebate = () => {
    setView('createDebate')
    setError(null)
  }

  const handleBrowseTopics = () => {
    setView('browse')
    setError(null)
  }

  const handleSelectTopic = (topic: TopicListItem) => {
    setSelectedTopicId(topic.id)
    setView('topic')
    setError(null)
  }

  const handleBackToLanding = () => {
    setView('landing')
    setSelectedTopic(null)
    setSelectedTopicId(null)
    setError(null)
  }

  const handleBackToBrowse = () => {
    setView('browse')
    setSelectedTopic(null)
    setSelectedTopicId(null)
    setError(null)
  }

  const handleAddProArg = () => {
    setNewDebateForm(prev => ({
      ...prev,
      proArgs: [...prev.proArgs, { title: '', content: '', sources: '' }]
    }))
  }

  const handleAddConArg = () => {
    setNewDebateForm(prev => ({
      ...prev,
      conArgs: [...prev.conArgs, { title: '', content: '', sources: '' }]
    }))
  }

  const handleRemoveProArg = (index: number) => {
    setNewDebateForm(prev => ({
      ...prev,
      proArgs: prev.proArgs.filter((_, i) => i !== index)
    }))
  }

  const handleRemoveConArg = (index: number) => {
    setNewDebateForm(prev => ({
      ...prev,
      conArgs: prev.conArgs.filter((_, i) => i !== index)
    }))
  }

  const handleSubmitDebate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Validate that we have at least one pro and one con argument
      if (newDebateForm.proArgs.length === 0 || newDebateForm.conArgs.length === 0) {
        throw new Error('Please provide at least one pro argument and one con argument')
      }

      // Create the topic
      const topicResponse = await createTopic({
        question: newDebateForm.title,
        created_by: newDebateForm.createdBy
      })

      const topicId = topicResponse.topic_id

      // Create pro arguments
      for (const arg of newDebateForm.proArgs) {
        if (arg.title.trim() && arg.content.trim()) {
          await createArgument(topicId, {
            side: 'pro',
            title: arg.title,
            content: arg.content,
            sources: arg.sources || undefined,
            author: newDebateForm.createdBy
          })
        }
      }

      // Create con arguments
      for (const arg of newDebateForm.conArgs) {
        if (arg.title.trim() && arg.content.trim()) {
          await createArgument(topicId, {
            side: 'con',
            title: arg.title,
            content: arg.content,
            sources: arg.sources || undefined,
            author: newDebateForm.createdBy
          })
        }
      }

      // Reset form and navigate
      setNewDebateForm({
        title: '',
        createdBy: 'user',
        proArgs: [{ title: '', content: '', sources: '' }],
        conArgs: [{ title: '', content: '', sources: '' }]
      })
      setView('browse')
      // Refresh topics list
      await fetchTopics()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create debate')
      console.error('Error creating debate:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleBackFromCreate = () => {
    setView('landing')
    setError(null)
    setNewDebateForm({
      title: '',
      createdBy: 'user',
      proArgs: [{ title: '', content: '', sources: '' }],
      conArgs: [{ title: '', content: '', sources: '' }]
    })
  }

  const handleAddArgument = async (side: 'pro' | 'con') => {
    if (!selectedTopicId) return

    setLoading(true)
    setError(null)

    try {
      await createArgument(selectedTopicId, {
        side,
        title: newArgument.title,
        content: newArgument.content,
        sources: newArgument.sources || undefined,
        author: 'user' // Default username
      })

      // Reset form and refresh topic
      setNewArgument({ title: '', content: '', sources: '', side: 'pro' })
      setShowAddArgumentForm({ side: null })
      await fetchTopicDetails(selectedTopicId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add argument')
      console.error('Error adding argument:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyArgument = async (argumentId: number) => {
    setVerifyingArgumentId(argumentId)
    setError(null)

    try {
      await verifyArgument(argumentId)
      // Refetch topic to get updated validity scores
      if (selectedTopicId) {
        await fetchTopicDetails(selectedTopicId)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to verify argument')
      console.error('Error verifying argument:', err)
    } finally {
      setVerifyingArgumentId(null)
    }
  }


  if (view === 'createDebate') {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="fixed inset-0 bg-grid-pattern opacity-20 pointer-events-none" />
        
        <div className="relative px-6 py-12 max-w-7xl mx-auto">
          <Button 
            variant="ghost" 
            className="text-gray-400 hover:text-white mb-8"
            onClick={handleBackFromCreate}
            disabled={loading}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>

          <div className="mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Create New Debate</h1>
            <p className="text-xl text-gray-400">Start a structured discussion on any topic</p>
          </div>

          {error && (
            <Card className="bg-red-950/30 border-red-500/30 p-4 mb-6">
              <p className="text-red-400">{error}</p>
            </Card>
          )}

          <form onSubmit={handleSubmitDebate} className="space-y-8">
            {/* Topic Title */}
            <Card className="bg-[#1a1a1a] border-[#2a2a2a] p-8">
              <label className="block mb-3 text-lg font-semibold">Debate Topic</label>
              <Input
                required
                value={newDebateForm.title}
                onChange={(e) => setNewDebateForm(prev => ({ ...prev, title: e.target.value }))}
                placeholder="e.g., Should remote work be the default?"
                className="bg-black border-gray-700 text-white text-lg py-6"
              />
              <p className="text-sm text-gray-500 mt-2">Frame as a clear question that has multiple valid perspectives</p>
            </Card>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Pro Arguments Column */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="w-1 h-6 bg-green-500 rounded-full" />
                    <h3 className="text-xl font-semibold text-green-500">Pro Arguments</h3>
                  </div>
                  <Button 
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={handleAddProArg}
                    className="border-green-500/30 hover:bg-green-950/30 text-green-500"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add
                  </Button>
                </div>

                <div className="space-y-4">
                  {newDebateForm.proArgs.map((arg, index) => (
                    <Card key={index} className="bg-[#0f1f0f] border-green-900/30 p-6">
                      <div className="flex justify-between items-start mb-3">
                        <label className="text-sm font-medium text-green-400">Argument {index + 1}</label>
                        {newDebateForm.proArgs.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveProArg(index)}
                            className="text-gray-500 hover:text-red-400 h-auto p-1"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                      <Input
                        required
                        value={arg.title}
                        onChange={(e) => {
                          const newProArgs = [...newDebateForm.proArgs]
                          newProArgs[index].title = e.target.value
                          setNewDebateForm(prev => ({ ...prev, proArgs: newProArgs }))
                        }}
                        placeholder="Argument title..."
                        className="bg-black/50 border-green-800/30 text-white mb-3"
                      />
                      <Textarea
                        required
                        value={arg.content}
                        onChange={(e) => {
                          const newProArgs = [...newDebateForm.proArgs]
                          newProArgs[index].content = e.target.value
                          setNewDebateForm(prev => ({ ...prev, proArgs: newProArgs }))
                        }}
                        placeholder="Describe the pro argument..."
                        className="bg-black/50 border-green-800/30 text-white mb-3 min-h-[100px]"
                      />
                      <Input
                        value={arg.sources}
                        onChange={(e) => {
                          const newProArgs = [...newDebateForm.proArgs]
                          newProArgs[index].sources = e.target.value
                          setNewDebateForm(prev => ({ ...prev, proArgs: newProArgs }))
                        }}
                        placeholder="Sources (optional)"
                        className="bg-black/50 border-green-800/30 text-white"
                      />
                    </Card>
                  ))}
                </div>
              </div>

              {/* Con Arguments Column */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="w-1 h-6 bg-rose-500 rounded-full" />
                    <h3 className="text-xl font-semibold text-rose-500">Con Arguments</h3>
                  </div>
                  <Button 
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={handleAddConArg}
                    className="border-rose-500/30 hover:bg-rose-950/30 text-rose-500"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add
                  </Button>
                </div>

                <div className="space-y-4">
                  {newDebateForm.conArgs.map((arg, index) => (
                    <Card key={index} className="bg-[#1f0f0f] border-rose-900/30 p-6">
                      <div className="flex justify-between items-start mb-3">
                        <label className="text-sm font-medium text-rose-400">Argument {index + 1}</label>
                        {newDebateForm.conArgs.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveConArg(index)}
                            className="text-gray-500 hover:text-red-400 h-auto p-1"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                      <Input
                        required
                        value={arg.title}
                        onChange={(e) => {
                          const newConArgs = [...newDebateForm.conArgs]
                          newConArgs[index].title = e.target.value
                          setNewDebateForm(prev => ({ ...prev, conArgs: newConArgs }))
                        }}
                        placeholder="Argument title..."
                        className="bg-black/50 border-rose-800/30 text-white mb-3"
                      />
                      <Textarea
                        required
                        value={arg.content}
                        onChange={(e) => {
                          const newConArgs = [...newDebateForm.conArgs]
                          newConArgs[index].content = e.target.value
                          setNewDebateForm(prev => ({ ...prev, conArgs: newConArgs }))
                        }}
                        placeholder="Describe the con argument..."
                        className="bg-black/50 border-rose-800/30 text-white mb-3 min-h-[100px]"
                      />
                      <Input
                        value={arg.sources}
                        onChange={(e) => {
                          const newConArgs = [...newDebateForm.conArgs]
                          newConArgs[index].sources = e.target.value
                          setNewDebateForm(prev => ({ ...prev, conArgs: newConArgs }))
                        }}
                        placeholder="Sources (optional)"
                        className="bg-black/50 border-rose-800/30 text-white"
                      />
                    </Card>
                  ))}
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end gap-4 pt-6">
              <Button 
                type="button"
                variant="outline" 
                onClick={handleBackFromCreate}
                className="border-gray-700 hover:bg-gray-900 text-white px-8 py-6"
              >
                Cancel
              </Button>
              <Button 
                type="submit"
                disabled={loading}
                className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white border-0 px-8 py-6 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Debate'
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  if (view === 'browse') {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="fixed inset-0 bg-grid-pattern opacity-20 pointer-events-none" />
        
        <div className="relative px-6 py-12 max-w-7xl mx-auto">
          <Button 
            variant="ghost" 
            className="text-gray-400 hover:text-white mb-8"
            onClick={handleBackToLanding}
            disabled={loading}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>

          <div className="flex justify-between items-center mb-12">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-4">Browse Topics</h1>
              <p className="text-xl text-gray-400">Explore ongoing debates and contribute your perspective</p>
            </div>
            <Button 
              onClick={handleStartDebate}
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white border-0"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Topic
            </Button>
          </div>

          {error && (
            <Card className="bg-red-950/30 border-red-500/30 p-4 mb-6">
              <p className="text-red-400">{error}</p>
            </Card>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
            </div>
          ) : topics.length === 0 ? (
            <Card className="bg-[#1a1a1a] border-[#2a2a2a] p-12 text-center">
              <p className="text-gray-400 text-lg mb-4">No topics yet. Be the first to start a debate!</p>
              <Button 
                onClick={handleStartDebate}
                className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white border-0"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Topic
              </Button>
            </Card>
          ) : (
            <div className="space-y-6">
              {topics.map((topic) => (
                <Card 
                  key={topic.id}
                  className="bg-[#1a1a1a] border-[#2a2a2a] p-8 hover:bg-[#1f1f1f] transition-all duration-300 cursor-pointer hover:border-purple-500/30"
                  onClick={() => handleSelectTopic(topic)}
                >
                  <h3 className="text-2xl font-semibold mb-4">{topic.question}</h3>
                  <div className="flex gap-8 text-sm text-gray-400">
                    <span className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full" />
                      {topic.pro_count} Pro Arguments
                    </span>
                    <span className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-rose-500 rounded-full" />
                      {topic.con_count} Con Arguments
                    </span>
                    {topic.pro_count > 0 && topic.con_count > 0 && (
                      <span className="flex items-center gap-2">
                        <Brain className="w-4 h-4 text-purple-400" />
                        Ready for Analysis
                      </span>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  if (view === 'topic') {
    if (loading && !selectedTopic) {
      return (
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
          <p className="text-gray-400 text-lg">Verifying arguments and generating analysis...</p>
          <p className="text-gray-500 text-sm">This may take 30-60 seconds on first load</p>
        </div>
      )
    }

    if (!selectedTopic) {
      return (
        <div className="min-h-screen bg-black text-white">
          <div className="relative px-6 py-12 max-w-7xl mx-auto">
            <Button 
              variant="ghost" 
              className="text-gray-400 hover:text-white mb-8"
              onClick={handleBackToBrowse}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Topics
            </Button>
            <Card className="bg-[#1a1a1a] border-[#2a2a2a] p-12 text-center">
              <p className="text-gray-400 text-lg">Topic not found</p>
            </Card>
          </div>
        </div>
      )
    }

    return (
      <div className="min-h-screen bg-black text-white">
        <div className="fixed inset-0 bg-grid-pattern opacity-20 pointer-events-none" />
        
        <div className="relative px-6 py-12 max-w-7xl mx-auto">
          <Button 
            variant="ghost" 
            className="text-gray-400 hover:text-white mb-8"
            onClick={handleBackToBrowse}
            disabled={loading}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Topics
          </Button>

          {error && (
            <Card className="bg-red-950/30 border-red-500/30 p-4 mb-6">
              <p className="text-red-400">{error}</p>
            </Card>
          )}

          <div className="mb-12">
            <div className="flex items-center gap-3 mb-4">
              <span className="font-mono text-sm text-gray-500">TOPIC</span>
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold">{selectedTopic.question}</h1>
              <p className="text-sm text-gray-500 mt-2">Arguments sorted by validity (highest quality first)</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            {/* Pro Column */}
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-1 h-6 bg-green-500 rounded-full" />
                  <h4 className="text-lg font-semibold text-green-500">Pro Arguments</h4>
                </div>
                <Button 
                  size="sm"
                  variant="outline"
                  className="border-green-500/30 hover:bg-green-950/30 text-green-500"
                  onClick={() => setShowAddArgumentForm({ side: 'pro' })}
                  disabled={loading}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add
                </Button>
              </div>

              {showAddArgumentForm.side === 'pro' && (
                <Card className="bg-[#0f1f0f] border-green-900/30 p-6">
                  <Input
                    value={newArgument.title}
                    onChange={(e) => setNewArgument(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Argument title..."
                    className="bg-black/50 border-green-800/30 text-white mb-3"
                  />
                  <Textarea
                    value={newArgument.content}
                    onChange={(e) => setNewArgument(prev => ({ ...prev, content: e.target.value }))}
                    placeholder="Argument content..."
                    className="bg-black/50 border-green-800/30 text-white mb-3 min-h-[100px]"
                  />
                  <Input
                    value={newArgument.sources}
                    onChange={(e) => setNewArgument(prev => ({ ...prev, sources: e.target.value }))}
                    placeholder="Sources (optional)"
                    className="bg-black/50 border-green-800/30 text-white mb-3"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleAddArgument('pro')}
                      disabled={loading || !newArgument.title.trim() || !newArgument.content.trim()}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Submit'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setShowAddArgumentForm({ side: null })
                        setNewArgument({ title: '', content: '', sources: '', side: 'pro' })
                      }}
                      className="border-green-500/30 text-green-500"
                    >
                      Cancel
                    </Button>
                  </div>
                </Card>
              )}
              
              {selectedTopic.pro_arguments.length === 0 ? (
                <Card className="bg-[#0f1f0f] border-green-900/30 p-6 text-center">
                  <p className="text-gray-500 text-sm">No pro arguments yet</p>
                </Card>
              ) : (
                selectedTopic.pro_arguments.map((arg) => {
                  // Debug: log argument data
                  if (process.env.NODE_ENV === 'development') {
                    console.log('Pro argument:', arg.id, 'validity_score:', arg.validity_score, 'validity_reasoning:', arg.validity_reasoning)
                  }
                  
                  const validityScore = typeof arg.validity_score === 'number' ? arg.validity_score : 
                                       arg.validity_score !== null && arg.validity_score !== undefined ? 
                                       parseInt(String(arg.validity_score)) : null
                  
                  return (
                  <Card key={arg.id} className="bg-[#0f1f0f] border-green-900/30 p-6 hover:border-green-500/50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <h5 className="text-green-400 font-semibold flex-1">{arg.title}</h5>
                      {validityScore !== null && validityScore !== undefined && validityScore > 0 ? (
                        <div className="flex items-center gap-0.5 ml-2 flex-shrink-0 bg-yellow-950/20 px-2 py-1 rounded border border-yellow-500/30">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-4 h-4 ${
                                i < validityScore
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-gray-500 fill-transparent'
                              }`}
                            />
                          ))}
                          <span className="text-xs text-yellow-400 ml-1.5 font-semibold">{validityScore}/5</span>
                        </div>
                      ) : null}
                    </div>
                    <p className="text-gray-300 mb-3">{arg.content}</p>
                    {arg.validity_reasoning && (
                      <div className="mb-3 p-3 bg-black/30 rounded border border-yellow-500/20">
                        <p className="text-xs text-yellow-300 font-semibold mb-1">Fact-Check:</p>
                        <p className="text-xs text-gray-400">{arg.validity_reasoning}</p>
                      </div>
                    )}
                    <div className="flex justify-between items-center mt-3">
                      <div className="flex gap-2">
                        {arg.sources && (
                          <span className="text-xs text-gray-500 font-mono">Sources: {arg.sources}</span>
                        )}
                        <span className="text-xs text-gray-500 font-mono">by {arg.author}</span>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleVerifyArgument(arg.id)}
                        disabled={verifyingArgumentId === arg.id}
                        className="text-green-400 hover:text-green-300 hover:bg-green-950/30 h-auto py-1 text-xs"
                      >
                        {verifyingArgumentId === arg.id ? (
                          <>
                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            Verifying...
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Verify
                          </>
                        )}
                      </Button>
                    </div>
                  </Card>
                  )
                })
              )}
            </div>

            {/* Con Column */}
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-1 h-6 bg-rose-500 rounded-full" />
                  <h4 className="text-lg font-semibold text-rose-500">Con Arguments</h4>
                </div>
                <Button 
                  size="sm"
                  variant="outline"
                  className="border-rose-500/30 hover:bg-rose-950/30 text-rose-500"
                  onClick={() => setShowAddArgumentForm({ side: 'con' })}
                  disabled={loading}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add
                </Button>
              </div>

              {showAddArgumentForm.side === 'con' && (
                <Card className="bg-[#1f0f0f] border-rose-900/30 p-6">
                  <Input
                    value={newArgument.title}
                    onChange={(e) => setNewArgument(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Argument title..."
                    className="bg-black/50 border-rose-800/30 text-white mb-3"
                  />
                  <Textarea
                    value={newArgument.content}
                    onChange={(e) => setNewArgument(prev => ({ ...prev, content: e.target.value }))}
                    placeholder="Argument content..."
                    className="bg-black/50 border-rose-800/30 text-white mb-3 min-h-[100px]"
                  />
                  <Input
                    value={newArgument.sources}
                    onChange={(e) => setNewArgument(prev => ({ ...prev, sources: e.target.value }))}
                    placeholder="Sources (optional)"
                    className="bg-black/50 border-rose-800/30 text-white mb-3"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleAddArgument('con')}
                      disabled={loading || !newArgument.title.trim() || !newArgument.content.trim()}
                      className="bg-rose-600 hover:bg-rose-700 text-white"
                    >
                      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Submit'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setShowAddArgumentForm({ side: null })
                        setNewArgument({ title: '', content: '', sources: '', side: 'con' })
                      }}
                      className="border-rose-500/30 text-rose-500"
                    >
                      Cancel
                    </Button>
                  </div>
                </Card>
              )}
              
              {selectedTopic.con_arguments.length === 0 ? (
                <Card className="bg-[#1f0f0f] border-rose-900/30 p-6 text-center">
                  <p className="text-gray-500 text-sm">No con arguments yet</p>
                </Card>
              ) : (
                selectedTopic.con_arguments.map((arg) => {
                  // Debug: log argument data
                  if (process.env.NODE_ENV === 'development') {
                    console.log('Con argument:', arg.id, 'validity_score:', arg.validity_score, 'validity_reasoning:', arg.validity_reasoning)
                  }
                  
                  const validityScore = typeof arg.validity_score === 'number' ? arg.validity_score : 
                                       arg.validity_score !== null && arg.validity_score !== undefined ? 
                                       parseInt(String(arg.validity_score)) : null
                  
                  return (
                  <Card key={arg.id} className="bg-[#1f0f0f] border-rose-900/30 p-6 hover:border-rose-500/50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <h5 className="text-rose-400 font-semibold flex-1">{arg.title}</h5>
                      {validityScore !== null && validityScore !== undefined && validityScore > 0 ? (
                        <div className="flex items-center gap-0.5 ml-2 flex-shrink-0 bg-yellow-950/20 px-2 py-1 rounded border border-yellow-500/30">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-4 h-4 ${
                                i < validityScore
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-gray-500 fill-transparent'
                              }`}
                            />
                          ))}
                          <span className="text-xs text-yellow-400 ml-1.5 font-semibold">{validityScore}/5</span>
                        </div>
                      ) : null}
                    </div>
                    <p className="text-gray-300 mb-3">{arg.content}</p>
                    {arg.validity_reasoning && (
                      <div className="mb-3 p-3 bg-black/30 rounded border border-yellow-500/20">
                        <p className="text-xs text-yellow-300 font-semibold mb-1">Fact-Check:</p>
                        <p className="text-xs text-gray-400">{arg.validity_reasoning}</p>
                      </div>
                    )}
                    <div className="flex justify-between items-center mt-3">
                      <div className="flex gap-2">
                        {arg.sources && (
                          <span className="text-xs text-gray-500 font-mono">Sources: {arg.sources}</span>
                        )}
                        <span className="text-xs text-gray-500 font-mono">by {arg.author}</span>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleVerifyArgument(arg.id)}
                        disabled={verifyingArgumentId === arg.id}
                        className="text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 h-auto py-1 text-xs"
                      >
                        {verifyingArgumentId === arg.id ? (
                          <>
                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            Verifying...
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Verify
                          </>
                        )}
                      </Button>
                    </div>
                  </Card>
                  )
                })
              )}
            </div>
          </div>

          {/* AI Analysis Section */}
          <Card className="bg-gradient-to-br from-purple-950/30 to-purple-900/20 border-purple-500/30 p-8">
            <div className="flex items-center gap-3 mb-4">
              <Brain className="w-6 h-6 text-purple-400" />
              <h4 className="text-lg font-semibold text-purple-300">Claude Analysis</h4>
              {selectedTopic.overall_summary && (
                <span className="ml-auto text-xs text-purple-400 font-mono">Available</span>
              )}
            </div>
            
            {loading && !selectedTopic.overall_summary ? (
              <div className="flex items-center gap-2 text-purple-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating analysis...</span>
              </div>
            ) : selectedTopic.overall_summary ? (
              <div className="space-y-6">
                <div>
                  <h5 className="text-purple-300 font-semibold mb-2">Overall Summary</h5>
                  <p className="text-gray-300 leading-relaxed">{selectedTopic.overall_summary}</p>
                </div>
                {selectedTopic.consensus_view && (
                  <div>
                    <h5 className="text-purple-300 font-semibold mb-2">Consensus View</h5>
                    <p className="text-gray-300 leading-relaxed">{selectedTopic.consensus_view}</p>
                  </div>
                )}
                {selectedTopic.timeline_view && selectedTopic.timeline_view.length > 0 && (
                  <div>
                    <h5 className="text-purple-300 font-semibold mb-2">Timeline View</h5>
                    <div className="space-y-3">
                      {selectedTopic.timeline_view.map((item, i) => (
                        <div key={i} className="border-l-2 border-purple-500/30 pl-4">
                          <p className="text-purple-400 font-semibold text-sm mb-1">{item.period}</p>
                          <p className="text-gray-300 text-sm">{item.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div>
                <p className="text-gray-400">
                  {selectedTopic.pro_arguments.length === 0 || selectedTopic.con_arguments.length === 0
                    ? 'Add at least one pro and one con argument to generate analysis'
                    : 'Analysis will be generated automatically...'}
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Background Grid Pattern */}
      <div className="fixed inset-0 bg-grid-pattern opacity-20 pointer-events-none" />
      
      {/* Hero Section */}
      <section className="relative px-6 py-20 md:py-32 max-w-7xl mx-auto">
        <div className="text-center space-y-8">
          {/* Animated Visualization */}
          <div className="mb-12 flex justify-center">
            <div className="relative w-full max-w-2xl h-32">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-600 to-purple-700 flex items-center justify-center animate-pulse-slow">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
              </div>
              {/* Pro side */}
              <div className="absolute left-0 top-1/2 -translate-y-1/2 flex gap-2 animate-slide-right">
                <div className="w-20 h-1 bg-green-500/60 rounded-full" />
                <div className="w-16 h-1 bg-green-500/40 rounded-full" />
              </div>
              {/* Con side */}
              <div className="absolute right-0 top-1/2 -translate-y-1/2 flex gap-2 animate-slide-left">
                <div className="w-16 h-1 bg-rose-500/40 rounded-full" />
                <div className="w-20 h-1 bg-rose-500/60 rounded-full" />
              </div>
            </div>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-balance">
            Every debate. Both sides.
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto text-pretty">
            Create topics, contribute arguments, let AI synthesize understanding. The resilient platform for structured discourse.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <Button 
              size="lg" 
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white border-0 text-lg px-8 py-6 transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-purple-500/50"
              onClick={handleStartDebate}
            >
              Start a Debate
            </Button>
            <Button 
              size="lg" 
              variant="outline" 
              className="border-gray-700 hover:bg-gray-900 text-white text-lg px-8 py-6 transition-all duration-300"
              onClick={handleBrowseTopics}
            >
              Browse Topics
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative px-6 py-20 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8">
          <Card className="bg-[#1a1a1a] border-[#2a2a2a] p-8 hover:bg-[#1f1f1f] transition-all duration-300 hover:scale-105 hover:shadow-xl">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-green-500/20 to-green-600/20 flex items-center justify-center mb-6">
              <Users className="w-6 h-6 text-green-500" />
            </div>
            <h3 className="text-2xl font-semibold mb-4">Community-Driven Arguments</h3>
            <p className="text-gray-400 text-lg leading-relaxed">
              Every topic starts with real perspectives. Users contribute pro and con arguments with sources.
            </p>
          </Card>

          <Card className="bg-[#1a1a1a] border-[#2a2a2a] p-8 hover:bg-[#1f1f1f] transition-all duration-300 hover:scale-105 hover:shadow-xl">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-700/20 flex items-center justify-center mb-6">
              <Brain className="w-6 h-6 text-purple-500" />
            </div>
            <h3 className="text-2xl font-semibold mb-4">AI Synthesis</h3>
            <p className="text-gray-400 text-lg leading-relaxed">
              Claude analyzes all arguments to generate summaries, identify consensus, and track how debates evolve.
            </p>
          </Card>

          <Card className="bg-[#1a1a1a] border-[#2a2a2a] p-8 hover:bg-[#1f1f1f] transition-all duration-300 hover:scale-105 hover:shadow-xl">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500/20 to-blue-600/20 flex items-center justify-center mb-6">
              <Scale className="w-6 h-6 text-blue-500" />
            </div>
            <h3 className="text-2xl font-semibold mb-4">Structured Discourse</h3>
            <p className="text-gray-400 text-lg leading-relaxed">
              Balanced presentation prevents echo chambers. See both sides, understand the nuances.
            </p>
          </Card>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="relative px-6 py-20 max-w-5xl mx-auto">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">How It Works</h2>
        
        <div className="space-y-12">
          {[
            {
              number: "01",
              title: "Create a Topic",
              description: "Submit a question with your initial pro and con arguments"
            },
            {
              number: "02",
              title: "Community Contributes",
              description: "Others add their perspectives and evidence"
            },
            {
              number: "03",
              title: "AI Synthesizes",
              description: "Generate analysis showing themes, consensus, and timeline"
            },
            {
              number: "04",
              title: "Understanding Emerges",
              description: "Navigate complex debates with clarity"
            }
          ].map((step, index) => (
            <div key={index} className="relative pl-24">
              {index < 3 && (
                <div className="absolute left-10 top-16 w-0.5 h-12 bg-gradient-to-b from-purple-600 to-purple-800" />
              )}
              <div className="absolute left-0 top-0 w-20 h-20 rounded-full bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center font-mono text-2xl font-bold shadow-lg shadow-purple-500/30">
                {step.number}
              </div>
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-8 hover:bg-[#1f1f1f] transition-all duration-300">
                <h3 className="text-2xl font-semibold mb-3">{step.title}</h3>
                <p className="text-gray-400 text-lg">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Sample Topic Preview */}
      <section className="relative px-6 py-20 max-w-7xl mx-auto">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">See It In Action</h2>
        
        <div className="relative bg-gradient-to-br from-[#1a1a1a] to-[#0a0a0a] border border-[#2a2a2a] rounded-2xl p-8 shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-transparent to-purple-500/5 rounded-2xl" />
          
          <div className="relative space-y-6">
            <div className="flex items-center gap-3 mb-8">
              <span className="font-mono text-sm text-gray-500">TOPIC</span>
              <h3 className="text-2xl font-semibold">Should remote work be the default?</h3>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Pro Column */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-1 h-6 bg-green-500 rounded-full" />
                  <h4 className="text-lg font-semibold text-green-500">Pro Arguments</h4>
                </div>
                
                {["Increased productivity and focus", "Better work-life balance", "Cost savings for companies"].map((arg, i) => (
                  <Card key={i} className="bg-[#0f1f0f] border-green-900/30 p-4 hover:border-green-500/50 transition-colors">
                    <p className="text-gray-300">{arg}</p>
                    <span className="text-xs text-gray-500 font-mono mt-2 block">+24 sources</span>
                  </Card>
                ))}
              </div>

              {/* Con Column */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-1 h-6 bg-rose-500 rounded-full" />
                  <h4 className="text-lg font-semibold text-rose-500">Con Arguments</h4>
                </div>
                
                {["Reduced team collaboration", "Isolation and mental health concerns", "Security and IP risks"].map((arg, i) => (
                  <Card key={i} className="bg-[#1f0f0f] border-rose-900/30 p-4 hover:border-rose-500/50 transition-colors">
                    <p className="text-gray-300">{arg}</p>
                    <span className="text-xs text-gray-500 font-mono mt-2 block">+18 sources</span>
                  </Card>
                ))}
              </div>
            </div>

            {/* AI Analysis Section */}
            <Card className="bg-gradient-to-br from-purple-950/30 to-purple-900/20 border-purple-500/30 p-6 mt-8">
              <div className="flex items-center gap-3 mb-4">
                <Brain className="w-6 h-6 text-purple-400" />
                <h4 className="text-lg font-semibold text-purple-300">Claude Analysis</h4>
                <span className="ml-auto text-xs text-purple-400 font-mono">Generated 2 min ago</span>
              </div>
              <p className="text-gray-300 leading-relaxed">
                The debate reveals a nuanced consensus: remote work offers significant individual benefits but requires intentional systems for collaboration. Most effective organizations adopt hybrid models that preserve autonomy while maintaining connection...
              </p>
              <Button 
                variant="ghost" 
                className="mt-4 text-purple-400 hover:text-purple-300 hover:bg-purple-950/50"
              >
                Read Full Analysis →
              </Button>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative px-6 py-12 border-t border-[#2a2a2a] mt-20">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-center md:text-left">
              <h3 className="text-2xl font-bold mb-2">Debately</h3>
              <p className="text-gray-500 text-sm">Build understanding through structured debate</p>
            </div>
            
            <div className="flex gap-8 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">About</a>
              <a href="#" className="hover:text-white transition-colors">Features</a>
              <a href="#" className="hover:text-white transition-colors">Pricing</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
          </div>
          
          <div className="text-center mt-8 text-sm text-gray-500 font-mono">
            Built for Claude Builders Hackathon 2024
          </div>
        </div>
      </footer>
    </div>
  )
}
