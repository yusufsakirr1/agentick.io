import { doc, getDoc, setDoc, updateDoc, arrayUnion, arrayRemove } from 'firebase/firestore'
import { db } from '../config/firebase'

export interface Holding {
  ticker: string
  shares: number
  avgCost: number
  addedAt: string
}

function portfolioRef(uid: string) {
  return doc(db, 'users', uid, 'portfolios', 'default')
}

export async function getPortfolio(uid: string): Promise<Holding[]> {
  const snap = await getDoc(portfolioRef(uid))
  if (!snap.exists()) return []
  return (snap.data().holdings ?? []) as Holding[]
}

export async function addHolding(uid: string, holding: Holding): Promise<void> {
  const ref = portfolioRef(uid)
  const snap = await getDoc(ref)
  if (!snap.exists()) {
    await setDoc(ref, { holdings: [holding] })
  } else {
    await updateDoc(ref, { holdings: arrayUnion(holding) })
  }
}

export async function updateHolding(uid: string, holdings: Holding[]): Promise<void> {
  const ref = portfolioRef(uid)
  await setDoc(ref, { holdings }, { merge: true })
}

export async function removeHolding(uid: string, holding: Holding): Promise<void> {
  await updateDoc(portfolioRef(uid), { holdings: arrayRemove(holding) })
}
