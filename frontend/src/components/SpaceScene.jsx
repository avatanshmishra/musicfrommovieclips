import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Sparkles, Stars, Float, Sphere, MeshDistortMaterial, Torus } from '@react-three/drei'
import { useRef } from 'react'

function BlackHole() {
  const ref = useRef()
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.z += delta * 0.35
  })

  return (
    <Float speed={1.5} rotationIntensity={0.4} floatIntensity={0.8}>
      <group ref={ref}>
        <Sphere args={[1.2, 64, 64]}>
          <MeshDistortMaterial color="#05060f" distort={0.35} speed={2.5} roughness={0.1} metalness={0.9} />
        </Sphere>
        <Torus args={[2.2, 0.18, 24, 120]} rotation={[1.5, 0.2, 0.4]}>
          <meshStandardMaterial color="#d3ad7f" emissive="#7b5c35" emissiveIntensity={1.2} />
        </Torus>
      </group>
    </Float>
  )
}

function Planet() {
  const ref = useRef()
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.15
  })

  return (
    <Float speed={1.2} rotationIntensity={0.15} floatIntensity={0.35}>
      <mesh ref={ref} position={[4, -1.4, -2]}>
        <sphereGeometry args={[0.9, 64, 64]} />
        <meshStandardMaterial color="#6782a4" roughness={0.8} metalness={0.1} />
      </mesh>
    </Float>
  )
}

export default function SpaceScene() {
  return (
    <div className="space-canvas">
      <Canvas camera={{ position: [0, 0, 8], fov: 55 }}>
        <color attach="background" args={['#02040b']} />
        <ambientLight intensity={0.8} />
        <pointLight position={[4, 3, 5]} intensity={13} color="#f6d4a3" />
        <pointLight position={[-4, -2, -3]} intensity={4} color="#7ea6ff" />
        <Stars radius={120} depth={50} count={3500} factor={4} saturation={0} fade speed={1} />
        <Sparkles count={180} scale={12} size={2.2} speed={0.4} />
        <BlackHole />
        <Planet />
        <OrbitControls enablePan={false} enableZoom={false} autoRotate autoRotateSpeed={0.3} />
      </Canvas>
    </div>
  )
}
