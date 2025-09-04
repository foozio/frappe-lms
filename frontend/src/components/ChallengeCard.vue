<template>
	<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
		<!-- Header -->
		<div class="flex items-start justify-between mb-4">
			<div class="flex-1">
				<h3 class="text-lg font-semibold text-gray-900 mb-1">{{ challenge.title }}</h3>
				<div class="flex items-center gap-2 mb-2">
					<span
						:class="[
							'px-2 py-1 rounded-full text-xs font-medium',
							challenge.challenge_type === 'daily' ? 'bg-blue-100 text-blue-700' :
							challenge.challenge_type === 'weekly' ? 'bg-green-100 text-green-700' :
							'bg-purple-100 text-purple-700'
						]"
					>
						{{ challenge.challenge_type.charAt(0).toUpperCase() + challenge.challenge_type.slice(1) }}
					</span>
					<PointsBadge :points="challenge.points_reward" variant="success" size="sm" />
				</div>
			</div>
			<div
				:class="[
					'px-3 py-1 rounded-full text-xs font-medium',
					challenge.status === 'completed' ? 'bg-green-100 text-green-700' :
					challenge.status === 'active' ? 'bg-blue-100 text-blue-700' :
					'bg-gray-100 text-gray-600'
				]"
			>
				{{ getStatusText() }}
			</div>
		</div>

		<!-- Description -->
		<p class="text-gray-600 text-sm mb-4 line-clamp-2">{{ challenge.description }}</p>

		<!-- Progress (for active challenges) -->
		<div v-if="challenge.status === 'active' && challenge.progress !== undefined" class="mb-4">
			<div class="flex justify-between text-sm text-gray-600 mb-1">
				<span>Progress</span>
				<span>{{ challenge.progress }}/{{ challenge.target_value }}</span>
			</div>
			<div class="w-full bg-gray-200 rounded-full h-2">
				<div
					class="bg-blue-500 h-2 rounded-full transition-all duration-300"
					:style="{ width: `${Math.min((challenge.progress / challenge.target_value) * 100, 100)}%` }"
				></div>
			</div>
		</div>

		<!-- Date Range -->
		<div class="flex items-center text-sm text-gray-500 mb-4">
			<span class="mr-1">📅</span>
			<span>{{ formatDateRange() }}</span>
		</div>

		<!-- Action Button -->
		<div class="flex justify-end">
			<button
				v-if="challenge.status === 'available'"
				@click="$emit('join', challenge.name)"
				class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
				:disabled="loading"
			>
				{{ loading ? 'Joining...' : 'Join Challenge' }}
			</button>
			<button
				v-else-if="challenge.status === 'active'"
				class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg cursor-not-allowed text-sm font-medium"
				disabled
			>
				In Progress
			</button>
			<button
				v-else-if="challenge.status === 'completed'"
				class="px-4 py-2 bg-green-100 text-green-600 rounded-lg cursor-not-allowed text-sm font-medium"
				disabled
			>
				✓ Completed
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import PointsBadge from './PointsBadge.vue'

const props = defineProps({
	challenge: {
		type: Object,
		required: true
	},
	loading: {
		type: Boolean,
		default: false
	}
})

const emit = defineEmits(['join'])

const getStatusText = () => {
	switch (props.challenge.status) {
		case 'completed': return 'Completed'
		case 'active': return 'Active'
		case 'available': return 'Available'
		default: return 'Unknown'
	}
}

const formatDateRange = () => {
	const startDate = new Date(props.challenge.start_date)
	const endDate = new Date(props.challenge.end_date)
	
	const formatDate = (date) => {
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric'
		})
	}
	
	return `${formatDate(startDate)} - ${formatDate(endDate)}`
}
</script>

<style scoped>
.line-clamp-2 {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}
</style>