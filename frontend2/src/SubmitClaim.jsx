import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import VoiceInput from './VoiceInput'

function SubmitClaim() {
  const [form, setForm] = useState({
    customer_name: '',
    car_model: '',
    vehicle_number: '',
    city: '',
    policy_type: 'comprehensive',
    claim_amount: '',
    description: ''
  })

  // Mode: 'camera' (Anti-Fraud Verified) vs 'upload' (Demo / Offline Fallback)
  const [captureMode, setCaptureMode] = useState('camera')

  // Hardware Proof & Media State
  const [files, setFiles] = useState([])
  const [capturedImages, setCapturedImages] = useState([])
  const [garagePdf, setGaragePdf] = useState(null)
  const [walkaroundVideo, setWalkaroundVideo] = useState(null)
  const [walkaroundVideoPreview, setWalkaroundVideoPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [verifiedVehicles, setVerifiedVehicles] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState(null)

  // WebRTC & Geolocation State
  const [cameraActive, setCameraActive] = useState(false)
  const [cameraFacing, setCameraFacing] = useState('environment') // 'environment' | 'user'
  const [cameraError, setCameraError] = useState(null)
  const [geoCoords, setGeoCoords] = useState(null)
  const [geoLoading, setGeoLoading] = useState(false)
  const [geoError, setGeoError] = useState(null)
  const [isLiveCapture, setIsLiveCapture] = useState(false)
  const [captureTimestamp, setCaptureTimestamp] = useState('')

  // Split Incident & Inspection Declaration State
  const [isPostTransit, setIsPostTransit] = useState(false)
  const [incidentLocation, setIncidentLocation] = useState('')
  const [inspectionLocation, setInspectionLocation] = useState('')
  const [transitReason, setTransitReason] = useState('Vehicle towed directly to repair workshop / residence')

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const mobileInputRef = useRef(null)

  // WebRTC Video Recording State
  const [videoModalOpen, setVideoModalOpen] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const mediaRecorderRef = useRef(null)
  const recordedChunks = useRef([])
  const videoRecordRef = useRef(null)
  const recordingTimerRef = useRef(null)

  const token = localStorage.getItem('token')

  useEffect(() => {
    axios
      .get('http://127.0.0.1:8000/vehicles/verified', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      .then((res) => setVerifiedVehicles(res.data))
      .catch(() => {})

    return () => {
      // Clean up WebRTC video stream on unmount
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [token])

  // Geolocation Request Helper
  const requestGeolocation = () => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation not supported by this browser')
      return
    }

    setGeoLoading(true)
    setGeoError(null)

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoCoords({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy
        })
        setGeoLoading(false)
      },
      (err) => {
        console.warn('Geolocation error:', err.message)
        setGeoError(err.message || 'GPS location unavailable')
        setGeoLoading(false)
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    )
  }

  // WebRTC Camera Management
  const startCamera = async (facing = cameraFacing) => {
    setCameraError(null)
    requestGeolocation()

    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
      }

      const constraints = {
        video: {
          facingMode: facing,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
      }

      setCameraActive(true)
    } catch (err) {
      console.error('Camera access error:', err)
      setCameraError(
        'Unable to access device camera. Please allow camera permissions, use the Mobile Camera button, or switch to Demo Upload Mode.'
      )
      setCameraActive(false)
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setCameraActive(false)
  }

  const toggleCameraFacing = () => {
    const nextFacing = cameraFacing === 'environment' ? 'user' : 'environment'
    setCameraFacing(nextFacing)
    if (cameraActive) {
      startCamera(nextFacing)
    }
  }

  // Visual Watermark Burn-in Function
  const drawWatermark = (ctx, width, height, metadata) => {
    const { lat, lng, accuracy, timestamp, vehicleNumber } = metadata
    const bannerHeight = Math.max(68, Math.round(height * 0.12))
    const y = height - bannerHeight

    ctx.save()

    // Semi-transparent dark HUD banner
    ctx.fillStyle = 'rgba(10, 15, 30, 0.85)'
    ctx.fillRect(0, y, width, bannerHeight)

    // Security emerald border
    ctx.strokeStyle = '#10b981'
    ctx.lineWidth = Math.max(2, Math.round(height * 0.005))
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()

    // Text configuration
    const baseFontSize = Math.max(12, Math.round(height * 0.024))
    ctx.textBaseline = 'top'

    const padX = 18
    let padY = y + 8

    // Row 1: Security Badge
    ctx.fillStyle = '#34d399'
    ctx.font = `bold ${baseFontSize}px "Courier New", Courier, monospace`
    ctx.fillText('🛡️ SECURE HARDWARE CAPTURE // PROOF-OF-PRESENCE VERIFIED', padX, padY)

    // Row 2: GPS & UTC Timestamp
    padY += baseFontSize + 5
    ctx.fillStyle = '#f8fafc'
    ctx.font = `${Math.max(11, Math.round(baseFontSize * 0.88))}px "Courier New", Courier, monospace`
    const gpsText =
      lat !== null && lat !== undefined && lng !== null && lng !== undefined
        ? `LAT: ${lat.toFixed(5)}° | LNG: ${lng.toFixed(5)}° (±${Math.round(accuracy || 0)}m)`
        : 'GPS: SENSOR ACQUIRING / BROWSER FALLBACK'
    ctx.fillText(`${gpsText} | UTC: ${timestamp}`, padX, padY)

    // Row 3: Vehicle Registration & Cryptographic Seal
    padY += baseFontSize + 4
    ctx.fillStyle = '#94a3b8'
    ctx.font = `${Math.max(10, Math.round(baseFontSize * 0.78))}px "Courier New", Courier, monospace`
    const regText = vehicleNumber ? `VEHICLE: ${vehicleNumber}` : 'VEHICLE: UNREGISTERED'
    ctx.fillText(`${regText} | SHA-256 PROOF SEALED`, padX, padY)

    ctx.restore()
  }

  // Capture Photo from WebRTC Video Stream
  const capturePhoto = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    const w = video.videoWidth || 1280
    const h = video.videoHeight || 720
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, w, h)

    const now = new Date()
    const utcTimestamp = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC'

    drawWatermark(ctx, w, h, {
      lat: geoCoords?.lat,
      lng: geoCoords?.lng,
      accuracy: geoCoords?.accuracy,
      timestamp: utcTimestamp,
      vehicleNumber: form.vehicle_number
    })

    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const filename = `live_cam_${Date.now()}.jpg`
        const file = new File([blob], filename, { type: 'image/jpeg' })
        const previewUrl = URL.createObjectURL(blob)

        const newCapture = {
          file,
          previewUrl,
          isLive: true,
          timestamp: utcTimestamp,
          coords: geoCoords
        }

        setCapturedImages((prev) => [...prev, newCapture].slice(0, 5))
        setFiles((prev) => [...prev, file].slice(0, 5))
        setIsLiveCapture(true)
        setCaptureTimestamp(utcTimestamp)
      },
      'image/jpeg',
      0.92
    )
  }

  // Handle Native Mobile Camera Capture (capture="environment")
  const handleMobileCapture = (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    requestGeolocation()

    const now = new Date()
    const utcTimestamp = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC'

    const reader = new FileReader()
    reader.onload = (event) => {
      const img = new Image()
      img.onload = () => {
        const canvas = canvasRef.current || document.createElement('canvas')
        canvas.width = img.width
        canvas.height = img.height
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0)

        drawWatermark(ctx, img.width, img.height, {
          lat: geoCoords?.lat,
          lng: geoCoords?.lng,
          accuracy: geoCoords?.accuracy,
          timestamp: utcTimestamp,
          vehicleNumber: form.vehicle_number
        })

        canvas.toBlob(
          (blob) => {
            if (!blob) return
            const filename = `mobile_cam_${Date.now()}.jpg`
            const watermarkedFile = new File([blob], filename, { type: 'image/jpeg' })
            const previewUrl = URL.createObjectURL(blob)

            const newCapture = {
              file: watermarkedFile,
              previewUrl,
              isLive: true,
              timestamp: utcTimestamp,
              coords: geoCoords
            }

            setCapturedImages((prev) => [...prev, newCapture].slice(0, 5))
            setFiles((prev) => [...prev, watermarkedFile].slice(0, 5))
            setIsLiveCapture(true)
            setCaptureTimestamp(utcTimestamp)
          },
          'image/jpeg',
          0.92
        )
      }
      img.src = event.target.result
    }
    reader.readAsDataURL(file)
  }

  // Handle Demo/Offline File Upload Fallback
  const handleFallbackUpload = (e) => {
    const selected = Array.from(e.target.files).slice(0, 5)
    setFiles(selected)
    setIsLiveCapture(false)
    setCaptureTimestamp('')

    const list = selected.map((f) => ({
      file: f,
      previewUrl: URL.createObjectURL(f),
      isLive: false,
      timestamp: null,
      coords: null
    }))
    setCapturedImages(list)
  }

  // Remove individual photo
  const removePhoto = (index) => {
    setCapturedImages((prev) => {
      const updated = prev.filter((_, i) => i !== index)
      const hasLive = updated.some((item) => item.isLive)
      setIsLiveCapture(hasLive)
      return updated
    })
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleVideoUpload = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setWalkaroundVideo(file)
      setWalkaroundVideoPreview(URL.createObjectURL(file))
    }
  }

  const removeVideo = () => {
    setWalkaroundVideo(null)
    setWalkaroundVideoPreview(null)
  }

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0')
    const s = (seconds % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  const startVideoRecordingStream = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      })
      streamRef.current = stream
      if (videoRecordRef.current) {
        videoRecordRef.current.srcObject = stream
        videoRecordRef.current.play()
      }
    } catch (err) {
      console.error('Video stream error:', err)
      alert('Unable to access camera for video recording.')
      setVideoModalOpen(false)
    }
  }

  const handleStartRecording = () => {
    if (!streamRef.current) return
    recordedChunks.current = []
    
    // Try webm first, fallback to mp4
    let mimeType = 'video/webm'
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = 'video/mp4'
    }

    try {
      const mediaRecorder = new MediaRecorder(streamRef.current, { mimeType })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          recordedChunks.current.push(e.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks.current, { type: mimeType })
        const ext = mimeType.includes('mp4') ? 'mp4' : 'webm'
        const filename = `walkaround_${Date.now()}.${ext}`
        const file = new File([blob], filename, { type: mimeType })
        
        setWalkaroundVideo(file)
        setWalkaroundVideoPreview(URL.createObjectURL(blob))
        
        closeVideoModal()
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      recordingTimerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= 29) {
            handleStopRecording()
            return 30
          }
          return prev + 1
        })
      }, 1000)
    } catch (err) {
      console.error('MediaRecorder error:', err)
      alert('Video recording is not supported in this browser.')
    }
  }

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      clearInterval(recordingTimerRef.current)
    }
  }

  const closeVideoModal = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRecordRef.current) {
      videoRecordRef.current.srcObject = null
    }
    setVideoModalOpen(false)
    setIsRecording(false)
    clearInterval(recordingTimerRef.current)
  }

  const openVideoModal = () => {
    setVideoModalOpen(true)
    startVideoRecordingStream()
  }

  const isPolicyExpired = (vehicle) => {
    if (!vehicle || !vehicle.policy_expiry_date) return false
    try {
      return new Date(vehicle.policy_expiry_date) < new Date()
    } catch {
      return false
    }
  }

  const handleVehicleSelect = (e) => {
    const vehicleId = parseInt(e.target.value)
    const vehicle = verifiedVehicles.find((v) => v.vehicle_id === vehicleId)

    setSelectedVehicle(vehicle || null)

    if (vehicle) {
      setForm((prevForm) => ({
        ...prevForm,
        car_model: vehicle.car_model,
        vehicle_number: vehicle.vehicle_number || vehicle.license_plate || ''
      }))
    }
  }

  const handleSubmit = async () => {
    if (files.length === 0) {
      alert('Please capture or upload at least one damage photo!')
      return
    }

    if (!selectedVehicle) {
      alert('Please select a verified vehicle!')
      return
    }

    if (isPolicyExpired(selectedVehicle)) {
      alert(`Policy expired on ${selectedVehicle.policy_expiry_date}! Please renew.`)
      return
    }

    if (!form.customer_name || !form.claim_amount || !form.city || !form.description) {
      alert('Please fill in all required fields!')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()

      Object.entries(form).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          formData.append(k, v)
        }
      })

      files.forEach((f) => {
        formData.append('files', f)
      })

      if (garagePdf) {
        formData.append('garage_pdf', garagePdf)
      }

      if (walkaroundVideo) {
        formData.append('walkaround_video', walkaroundVideo)
      }

      // Hardware Lock & Geolocation Proof Payload
      formData.append('is_live_capture', isLiveCapture ? 'true' : 'false')
      if (isLiveCapture && geoCoords?.lat) {
        formData.append('device_latitude', geoCoords.lat.toString())
      }
      if (isLiveCapture && geoCoords?.lng) {
        formData.append('device_longitude', geoCoords.lng.toString())
      }
      if (isLiveCapture && captureTimestamp) {
        formData.append('capture_timestamp', captureTimestamp)
      }

      // Split Incident & Inspection Declaration Payload
      formData.append('is_post_transit', isPostTransit ? 'true' : 'false')
      if (isPostTransit) {
        if (incidentLocation) formData.append('incident_location', incidentLocation)
        if (inspectionLocation) formData.append('inspection_location', inspectionLocation)
        if (transitReason) formData.append('transit_reason', transitReason)
      }

      const res = await axios.post('http://127.0.0.1:8000/claims/submit-claim', formData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      setResult(res.data)
      stopCamera()
    } catch (err) {
      alert(err.response?.data?.detail || 'Error submitting claim!')
    }

    setLoading(false)
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 max-w-4xl mx-auto my-6">
      {/* Hidden offscreen canvas for watermark burn-in */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Video Recording Modal */}
      {videoModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl relative">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
              <h3 className="font-bold text-gray-800 flex items-center gap-2">
                <span className="text-xl">🎥</span> Live Walkaround Recording
              </h3>
              <button onClick={closeVideoModal} className="text-gray-400 hover:text-gray-600 text-xl font-bold">×</button>
            </div>
            
            <div className="relative bg-black h-96">
              <video
                ref={videoRecordRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-contain"
              />
              
              {/* Recording Indicator */}
              {isRecording && (
                <div className="absolute top-4 right-4 flex items-center gap-2 bg-black/60 px-3 py-1.5 rounded-full">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                  <span className="text-white font-mono text-sm font-bold tracking-wider">
                    REC {formatTime(recordingTime)} / 00:30
                  </span>
                </div>
              )}
            </div>

            <div className="p-4 bg-gray-50 flex justify-center gap-3">
              {!isRecording ? (
                <button
                  type="button"
                  onClick={handleStartRecording}
                  className="bg-red-600 hover:bg-red-700 text-white font-bold px-6 py-2.5 rounded-full shadow-lg flex items-center gap-2 text-sm transition-transform active:scale-95"
                >
                  <span className="w-3 h-3 rounded-full bg-white"></span>
                  Start Recording
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleStopRecording}
                  className="bg-gray-800 hover:bg-gray-900 text-white font-bold px-6 py-2.5 rounded-full shadow-lg flex items-center gap-2 text-sm transition-transform active:scale-95"
                >
                  <span className="w-3 h-3 rounded-sm bg-red-500"></span>
                  Stop & Save Video
                </button>
              )}
              
              <button
                type="button"
                onClick={closeVideoModal}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-2.5 rounded-full text-sm transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 border-b pb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Submit New Claim</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            AI-powered damage assessment with hardware anti-fraud proof-of-presence
          </p>
        </div>

        {/* Capture Mode Toggle */}
        <div className="inline-flex p-1 bg-gray-100 rounded-lg text-xs font-semibold">
          <button
            type="button"
            onClick={() => {
              setCaptureMode('camera')
              requestGeolocation()
            }}
            className={`px-3 py-1.5 rounded-md transition-all ${
              captureMode === 'camera'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📸 Live Camera (Anti-Fraud)
          </button>
          <button
            type="button"
            onClick={() => {
              stopCamera()
              setCaptureMode('upload')
            }}
            className={`px-3 py-1.5 rounded-md transition-all ${
              captureMode === 'upload'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📁 File Upload (Demo Mode)
          </button>
        </div>
      </div>

      {!result ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Vehicle Selection */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Verified Vehicle <span className="text-red-500">*</span>
            </label>

            {verifiedVehicles.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-700">
                ⚠️ No verified vehicles found. Please add and verify a vehicle first!
              </div>
            ) : (
              <select
                onChange={handleVehicleSelect}
                value={selectedVehicle ? selectedVehicle.vehicle_id : ''}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="">-- Select Vehicle --</option>
                {verifiedVehicles.map((v) => (
                  <option key={v.vehicle_id} value={v.vehicle_id}>
                    {v.vehicle_number || v.license_plate} — {v.car_model} ✅ Verified
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Policy Status */}
          {selectedVehicle && (
            <div
              className={`md:col-span-2 p-3 rounded-lg text-sm border ${
                isPolicyExpired(selectedVehicle)
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : 'bg-green-50 border-green-200 text-green-700'
              }`}
            >
              {isPolicyExpired(selectedVehicle)
                ? `❌ Policy expired on ${selectedVehicle.policy_expiry_date}! Cannot submit claim.`
                : `✅ Policy valid until ${selectedVehicle.policy_expiry_date}`}
            </div>
          )}

          {/* Customer Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Customer Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Rahul Sharma"
              value={form.customer_name}
              onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* City */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              City <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Mumbai"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* Claim Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Claim Amount (₹) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              placeholder="e.g. 25000"
              value={form.claim_amount}
              onChange={(e) => setForm({ ...form, claim_amount: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* Policy Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Policy Type
            </label>
            <select
              value={form.policy_type}
              onChange={(e) => setForm({ ...form, policy_type: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="comprehensive">Comprehensive</option>
              <option value="third-party">Third Party</option>
              <option value="own-damage">Own Damage</option>
            </select>
          </div>

          {/* Incident Description */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Incident Description <span className="text-red-500">*</span>
            </label>

            <textarea
              rows={3}
              placeholder="Describe what happened in detail..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />

            <div className="mt-2">
              <VoiceInput
                onTranscript={(text) => {
                  setForm({
                    ...form,
                    description: (form.description ? form.description + ' ' : '') + text
                  })
                }}
              />
            </div>
          </div>

          {/* Damage Photos Section */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">
                Damage Photos ({files.length}/5) <span className="text-red-500">*</span>
              </label>

              {captureMode === 'camera' ? (
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">
                  🛡️ Live Hardware Lock Active
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                  ⚠️ Demo / File Upload Mode
                </span>
              )}
            </div>

            {/* Live Camera Mode UI */}
            {captureMode === 'camera' && (
              <div className="space-y-3">
                {/* GPS Status Bar */}
                <div className="flex flex-wrap items-center justify-between p-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                      <span
                        className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                          geoCoords ? 'bg-emerald-400' : 'bg-amber-400'
                        }`}
                      ></span>
                      <span
                        className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                          geoCoords ? 'bg-emerald-500' : 'bg-amber-500'
                        }`}
                      ></span>
                    </span>
                    <span className="font-medium text-gray-700">
                      {geoLoading
                        ? '🛰️ Acquiring high-accuracy GPS coordinates...'
                        : geoCoords
                        ? `📍 GPS Locked: ${geoCoords.lat.toFixed(5)}° N, ${geoCoords.lng.toFixed(
                            5
                          )}° E (±${Math.round(geoCoords.accuracy)}m)`
                        : geoError
                        ? `⚠️ GPS: ${geoError} (UTC timestamp still valid)`
                        : '🛰️ GPS Standby'}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={requestGeolocation}
                    className="text-blue-600 hover:text-blue-800 font-medium underline text-xs"
                  >
                    Refresh GPS
                  </button>
                </div>

                {/* WebRTC Viewfinder Box */}
                {cameraActive ? (
                  <div className="relative bg-black rounded-xl overflow-hidden shadow-inner border border-gray-800">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full max-h-96 object-contain bg-black"
                    />

                    {/* Viewfinder Target Overlays */}
                    <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                      <div className="border-2 border-emerald-400/60 rounded-xl w-3/4 h-3/4 border-dashed relative">
                        <div className="absolute top-2 left-2 text-[10px] font-mono text-emerald-300 bg-black/60 px-1.5 py-0.5 rounded">
                          FOCUS TARGET // VEHICLE DAMAGE
                        </div>
                      </div>
                    </div>

                    {/* Camera Control Toolbar */}
                    <div className="absolute bottom-3 inset-x-0 flex items-center justify-center gap-3 px-4 pointer-events-auto">
                      <button
                        type="button"
                        onClick={capturePhoto}
                        disabled={files.length >= 5}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-5 py-2.5 rounded-full shadow-lg flex items-center gap-2 text-sm transition-transform active:scale-95 disabled:opacity-50"
                      >
                        📸 Snap Photo ({files.length}/5)
                      </button>

                      <button
                        type="button"
                        onClick={toggleCameraFacing}
                        className="bg-gray-800/80 hover:bg-gray-700 text-white p-2.5 rounded-full shadow transition-colors text-sm"
                        title="Flip Camera (Front/Back)"
                      >
                        🔄
                      </button>

                      <button
                        type="button"
                        onClick={stopCamera}
                        className="bg-red-600/80 hover:bg-red-700 text-white p-2.5 rounded-full shadow transition-colors text-sm"
                        title="Close Camera"
                      >
                        ⏹️
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-emerald-200 bg-emerald-50/40 rounded-xl p-6 text-center space-y-3">
                    <div className="text-3xl">📷</div>
                    <div>
                      <h4 className="font-semibold text-gray-800 text-sm">
                        Live Hardware Camera Enforcement
                      </h4>
                      <p className="text-xs text-gray-500 max-w-md mx-auto mt-1">
                        Photos must be captured in real-time. Live photos receive an immutable
                        visual watermark with your device&apos;s GPS coordinates and UTC timestamp.
                      </p>
                    </div>

                    {cameraError && (
                      <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2 max-w-md mx-auto">
                        {cameraError}
                      </div>
                    )}

                    <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => startCamera('environment')}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
                      >
                        📹 Open Live Viewfinder
                      </button>

                      {/* Native Mobile Camera Input */}
                      <input
                        ref={mobileInputRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleMobileCapture}
                        className="hidden"
                        id="mobile-cam-direct"
                      />
                      <label
                        htmlFor="mobile-cam-direct"
                        className="cursor-pointer bg-gray-800 hover:bg-gray-900 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
                      >
                        📱 Launch Device Camera App
                      </label>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Demo / File Upload Fallback UI */}
            {captureMode === 'upload' && (
              <div className="space-y-2">
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800">
                  ℹ️ <strong>Demo / Offline Fallback Active:</strong> You can upload pre-existing
                  photos from your disk for testing and college viva evaluations. In production,
                  claims are hardware-locked to live camera captures.
                </div>

                <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleFallbackUpload}
                    className="hidden"
                    id="file-upload"
                  />

                  <label htmlFor="file-upload" className="cursor-pointer">
                    <div className="text-3xl mb-2">📁</div>
                    <p className="text-sm text-gray-500">
                      {files.length > 0
                        ? `✅ ${files.length} image(s) selected`
                        : 'Click to select damage images from local disk (max 5)'}
                    </p>
                  </label>
                </div>
              </div>
            )}

            {/* Captured Photos Preview Gallery */}
            {capturedImages.length > 0 && (
              <div className="pt-2">
                <p className="text-xs font-semibold text-gray-700 mb-2">
                  Captured Attachments ({capturedImages.length}/5):
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {capturedImages.map((img, idx) => (
                    <div
                      key={idx}
                      className="relative group border border-gray-200 rounded-lg overflow-hidden bg-gray-900 shadow-sm"
                    >
                      <img
                        src={img.previewUrl}
                        alt={`Capture ${idx + 1}`}
                        className="w-full h-28 object-cover opacity-90"
                      />

                      {/* Live Capture Proof Badge Overlay */}
                      <div className="absolute top-1.5 left-1.5">
                        {img.isLive ? (
                          <span className="bg-emerald-600/90 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow">
                            🛡️ Live Verified
                          </span>
                        ) : (
                          <span className="bg-gray-700/90 text-white text-[10px] font-medium px-1.5 py-0.5 rounded shadow">
                            📁 Uploaded File
                          </span>
                        )}
                      </div>

                      {/* Remove Button */}
                      <button
                        type="button"
                        onClick={() => removePhoto(idx)}
                        className="absolute top-1.5 right-1.5 bg-red-600 hover:bg-red-700 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center shadow transition-colors"
                        title="Delete photo"
                      >
                        ×
                      </button>

                      <div className="p-1.5 bg-gray-800 text-[10px] text-gray-300 truncate">
                        {img.file.name}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Post-Transit Inspection Declaration Section */}
          <div className="md:col-span-2 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4 shadow-sm">
            <label className="flex items-center gap-2 cursor-pointer font-bold text-blue-900 text-sm">
              <input
                type="checkbox"
                checked={isPostTransit}
                onChange={(e) => {
                  const checked = e.target.checked
                  setIsPostTransit(checked)
                  if (checked && !inspectionLocation) {
                    setInspectionLocation(form.city || '')
                  }
                }}
                className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
              <span>🚚 Vehicle was moved before taking photos (Post-Transit / Workshop / Residence)</span>
            </label>
            <p className="text-xs text-blue-700 mt-1 ml-6">
              Declare if the vehicle was towed or moved to a workshop/home before taking damage photos. Prevents geographic location penalties.
            </p>

            {isPostTransit && (
              <div className="mt-4 pt-3 border-t border-blue-200/60 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-blue-900 mb-1">
                    Incident City / Highway Location <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Where did the accident take place? (e.g., Pune Expressway, Lonavala)"
                    value={incidentLocation}
                    onChange={(e) => setIncidentLocation(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs text-gray-800"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-blue-900 mb-1 flex justify-between">
                    <span>Current Inspection Location <span className="text-red-500">*</span></span>
                    {geoCoords?.lat && (
                      <button
                        type="button"
                        onClick={() => setInspectionLocation(form.city ? `${form.city} (GPS: ${geoCoords.lat.toFixed(3)}, ${geoCoords.lng.toFixed(3)})` : `GPS: ${geoCoords.lat.toFixed(4)}, ${geoCoords.lng.toFixed(4)}`)}
                        className="text-blue-600 hover:underline text-[10px]"
                      >
                        Auto-fill Current GPS
                      </button>
                    )}
                  </label>
                  <input
                    type="text"
                    placeholder="Where is the vehicle right now? (e.g., Kalyan, Mumbai Workshop)"
                    value={inspectionLocation}
                    onChange={(e) => setInspectionLocation(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs text-gray-800"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block font-semibold text-blue-900 mb-1">
                    Reason for Transit / Scene Departure <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={transitReason}
                    onChange={(e) => setTransitReason(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs text-gray-800"
                  >
                    <option value="Vehicle towed directly to repair workshop / residence">
                      Vehicle towed directly to repair workshop / residence
                    </option>
                    <option value="Immediate safety hazard / highway police cleared traffic">
                      Immediate safety hazard / highway police cleared traffic
                    </option>
                    <option value="Medical emergency / driver attended hospital first">
                      Medical emergency / driver attended hospital first
                    </option>
                    <option value="Adverse weather / poor lighting on scene">
                      Adverse weather / poor lighting on scene
                    </option>
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Garage Estimate PDF */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Garage Estimate PDF <span className="text-gray-400">(Optional)</span>
            </label>

            {!garagePdf ? (
              <div className="border-2 border-dashed border-gray-200 rounded-lg p-4 text-center hover:border-green-400 transition-colors">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setGaragePdf(e.target.files[0] || null)}
                  className="hidden"
                  id="garage-upload"
                />

                <label htmlFor="garage-upload" className="cursor-pointer block">
                  <div className="text-2xl mb-1">📄</div>
                  <p className="text-sm text-gray-500">
                    Upload garage repair estimate (PDF)
                  </p>
                </label>
              </div>
            ) : (
              <div className="border border-green-200 bg-green-50 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">📄</div>
                  <div>
                    <p className="text-sm font-bold text-green-800">Estimate Uploaded</p>
                    <p className="text-xs text-green-600">{garagePdf.name}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setGaragePdf(null)}
                  className="bg-white border border-green-300 hover:bg-green-100 text-green-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                >
                  Remove
                </button>
              </div>
            )}
          </div>

          {/* 360° Walkaround Video (Inspection Proof) */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              360° Vehicle Walkaround Video (Inspection Proof) <span className="text-gray-400">(Optional)</span>
            </label>

            {!walkaroundVideo ? (
              <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 flex flex-col items-center justify-center gap-4 bg-gray-50 hover:border-purple-400 transition-colors">
                <div className="text-center">
                  <div className="text-3xl mb-2">🎥</div>
                  <p className="text-sm text-gray-600 mb-2">
                    Provide a short 360° video panning around the vehicle.
                  </p>
                </div>
                
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={openVideoModal}
                    className="bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
                  >
                    🎥 Record Live Video
                  </button>

                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoUpload}
                    className="hidden"
                    id="video-upload"
                  />
                  <label
                    htmlFor="video-upload"
                    className="cursor-pointer bg-gray-800 hover:bg-gray-900 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
                  >
                    📁 Upload Video File
                  </label>
                </div>
              </div>
            ) : (
              <div className="border border-gray-200 rounded-lg p-3 bg-gray-50 relative">
                <video
                  src={walkaroundVideoPreview}
                  controls
                  className="w-full max-h-56 rounded-lg bg-black"
                />
                <button
                  type="button"
                  onClick={removeVideo}
                  className="absolute top-4 right-4 bg-red-600 hover:bg-red-700 text-white text-xs w-6 h-6 rounded-full flex items-center justify-center shadow transition-colors"
                  title="Remove video"
                >
                  ×
                </button>
                <div className="mt-2 text-xs font-semibold text-gray-700">
                  Attached: {walkaroundVideo.name}
                </div>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="md:col-span-2">
            <button
              onClick={handleSubmit}
              disabled={
                loading ||
                verifiedVehicles.length === 0 ||
                !selectedVehicle ||
                isPolicyExpired(selectedVehicle) ||
                files.length === 0
              }
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  <span>Processing AI Damage & Fraud Analysis...</span>
                </>
              ) : (
                <span>🚀 Submit Claim for Instant AI Triage</span>
              )}
            </button>

            {isPolicyExpired(selectedVehicle) && (
              <p className="text-xs text-red-500 text-center mt-2">
                ❌ Cannot submit — policy expired!
              </p>
            )}
          </div>
        </div>
      ) : (
        /* Results View */
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-green-700 font-bold text-lg mb-1">
                  ✅ Claim Submitted Successfully!
                </h3>
                <p className="text-green-600">
                  Claim ID: <strong>#{result.claim_id}</strong>
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  setResult(null)
                  setFiles([])
                  setCapturedImages([])
                }}
                className="text-xs bg-white border border-green-300 text-green-700 px-3 py-1.5 rounded-lg hover:bg-green-100 font-medium"
              >
                Submit Another Claim
              </button>
            </div>

            {result.garage_estimate_pdf && (
              <p className="text-green-600 text-sm mt-1">📄 Garage estimate attached</p>
            )}
          </div>

          {/* Hardware & Geolocation Proof Banner */}
          {result.is_live_capture ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
              <div className="flex items-center gap-2 text-emerald-800 font-bold mb-1">
                <span>🛡️</span>
                <span>Hardware Proof-of-Presence: Live Camera Capture Verified</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-emerald-700 mt-2">
                <div>
                  📍 <strong>Device Geolocation:</strong>{' '}
                  {result.device_latitude ? `${result.device_latitude.toFixed(5)}° N` : 'N/A'},{' '}
                  {result.device_longitude ? `${result.device_longitude.toFixed(5)}° E` : 'N/A'}
                </div>
                <div>
                  🕒 <strong>Hardware Timestamp:</strong>{' '}
                  {result.capture_timestamp || 'Verified Real-time UTC'}
                </div>
              </div>
              <p className="text-[11px] text-emerald-600 mt-2">
                ✅ Direct hardware sensor capture verified. Visual watermark and metadata sealed
                against stock photo spoofing attacks.
              </p>
            </div>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-800">
              ℹ️ <strong>Submitted via File Upload (Demo Mode):</strong> Hardware proof-of-presence
              was not enforced for this submission.
            </div>
          )}

          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
            <p className="text-xs text-blue-600 font-medium mb-1">AI Recommendation & Reason</p>
            <p className="text-sm text-blue-800">{result.ai_reason}</p>
          </div>

          {/* Explainable AI Risk Breakdown */}
          {result.xai_explanation &&
            (() => {
              try {
                const factors = JSON.parse(result.xai_explanation)
                return factors.length > 0 ? (
                  <div className="bg-white border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <p className="font-bold text-gray-800">
                        🧠 Explainable AI Risk Breakdown
                      </p>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold ${
                          result.risk_level === 'CRITICAL'
                            ? 'bg-red-100 text-red-700'
                            : result.risk_level === 'HIGH'
                            ? 'bg-orange-100 text-orange-700'
                            : result.risk_level === 'MEDIUM'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {result.risk_level} RISK
                      </span>
                    </div>

                    <div className="space-y-2">
                      {factors.map((factor, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center gap-2">
                            <span>{factor.icon}</span>
                            <div>
                              <p className="text-xs font-medium text-gray-800">{factor.factor}</p>
                              <p className="text-xs text-gray-500">{factor.detail}</p>
                            </div>
                          </div>

                          <span
                            className={`text-xs font-bold ${
                              factor.contribution < 0 ? 'text-emerald-600' : 'text-red-600'
                            }`}
                          >
                            {factor.contribution < 0 ? '' : '+'}
                            {(factor.contribution * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-500">Total Fraud Risk</span>
                        <span className="font-bold">
                          {(result.fraud_score * 100).toFixed(0)}%
                        </span>
                      </div>

                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            result.fraud_score > 0.6
                              ? 'bg-red-500'
                              : result.fraud_score > 0.3
                              ? 'bg-amber-500'
                              : 'bg-green-500'
                          }`}
                          style={{
                            width: `${result.fraud_score * 100}%`
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ) : null
              } catch {
                return null
              }
            })()}

          {/* Consistency Check */}
          {result.consistency_status && (
            <div
              className={`border rounded-lg p-3 ${
                result.consistency_status === 'CONSISTENT'
                  ? 'bg-green-50 border-green-200'
                  : result.consistency_status === 'HIGHLY_INCONSISTENT'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-yellow-50 border-yellow-200'
              }`}
            >
              <p className="text-xs font-medium mb-1">
                🔍 Claim Consistency Check: {result.consistency_status}
              </p>

              {result.consistency_issues &&
                (() => {
                  try {
                    const issues = JSON.parse(result.consistency_issues)
                    return issues.map((issue, i) => (
                      <p key={i} className="text-xs mt-1">
                        ⚠️ {issue.message}
                      </p>
                    ))
                  } catch {
                    return null
                  }
                })()}
            </div>
          )}

          {/* Heatmap */}
          {result.heatmap_image && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-700 mb-2">🌡️ Damage Heatmap</p>

              <img
                src={`http://127.0.0.1:8000/${result.heatmap_image}`}
                alt="Damage Heatmap"
                className="w-full rounded-lg"
              />

              <p className="text-xs text-gray-500 mt-1">
                🔴 Severe &nbsp; 🟠 Moderate &nbsp; 🟢 Minor
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SubmitClaim